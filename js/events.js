/* SHEMA events: renders "Coming up" and "Past events" from /events.json,
   builds .ics downloads, Google Calendar links and Event JSON-LD.
   Pure functions are exported for tests (tests/test_events.py runs them in Node).
   No event is ever invented here: with no qualifying upcoming event the static
   "Next event to be announced" card stays in place. */
(function (root) {
  'use strict';

  var TZ = 'Australia/Melbourne';
  var SITE = 'https://shema.com.au';
  var CATEGORY_LABEL = { live: 'LIVE', show: 'SHOW', sport: 'SPORT', onam: 'ONAM', night: 'NIGHT', community: 'COMMUNITY' };
  var TILE = { live: 'live', show: 'show', sport: 'sport', onam: 'onam', night: 'night' };

  function melbourneToday(now) {
    return new Intl.DateTimeFormat('en-CA', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' }).format(now);
  }

  function isFinished(ev, now) {
    var end = ev.end || ev.start;
    if (ev.datePrecision === 'datetime') return new Date(end).getTime() <= now.getTime();
    if (ev.datePrecision === 'date') return end < melbourneToday(now);
    return true;
  }

  /* Returns { upcoming: [...max 3], past: [...] } following the plan's rules. */
  function splitEvents(data, now) {
    var events = (data && data.events) || [];
    var upcoming = [];
    var past = [];
    events.forEach(function (ev, index) {
      var datable = ev.datePrecision === 'datetime' || ev.datePrecision === 'date';
      var live = ev.status === 'upcoming' || ev.status === 'cancelled' || ev.status === 'postponed';
      var finished = isFinished(ev, now);
      if (live && datable && !finished) {
        upcoming.push({ ev: ev, index: index });
      } else if (ev.status === 'cancelled' || ev.status === 'postponed') {
        /* finished cancelled or postponed events are dropped */
      } else {
        past.push({ ev: ev, index: index });
      }
    });
    upcoming.sort(function (a, b) { return a.ev.start < b.ev.start ? -1 : a.ev.start > b.ev.start ? 1 : a.index - b.index; });
    past.sort(function (a, b) {
      var x = a.ev.start.slice(0, 10);
      var y = b.ev.start.slice(0, 10);
      return x < y ? 1 : x > y ? -1 : a.index - b.index;
    });
    return { upcoming: upcoming.slice(0, 3).map(function (o) { return o.ev; }), past: past.map(function (o) { return o.ev; }) };
  }

  function pad(n) { return (n < 10 ? '0' : '') + n; }

  function utcStamp(date) {
    return date.getUTCFullYear() + pad(date.getUTCMonth() + 1) + pad(date.getUTCDate()) + 'T' +
      pad(date.getUTCHours()) + pad(date.getUTCMinutes()) + pad(date.getUTCSeconds()) + 'Z';
  }

  function dateStamp(iso) { return iso.slice(0, 10).replace(/-/g, ''); }

  function nextDay(iso) {
    var d = new Date(iso.slice(0, 10) + 'T00:00:00Z');
    d.setUTCDate(d.getUTCDate() + 1);
    return d.getUTCFullYear() + pad(d.getUTCMonth() + 1) + pad(d.getUTCDate());
  }

  function eventTimes(ev) {
    if (ev.datePrecision === 'date') {
      return { allDay: true, start: dateStamp(ev.start), end: nextDay(ev.end || ev.start) };
    }
    var start = new Date(ev.start);
    var end = ev.end ? new Date(ev.end) : new Date(start.getTime() + 2 * 3600 * 1000);
    return { allDay: false, start: utcStamp(start), end: utcStamp(end) };
  }

  function locationText(venue) {
    if (!venue) return '';
    var tail = [venue.suburb, venue.state, venue.postcode].filter(Boolean).join(' ');
    return [venue.name, venue.address, tail].filter(Boolean).join(', ');
  }

  function icsEscape(text) {
    return String(text).replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n');
  }

  /* Fold at 75 octets (UTF-8), continuation lines start with one space. */
  function fold(line) {
    var out = [];
    var current = '';
    var bytes = 0;
    Array.from(line).forEach(function (ch) {
      var size = unescape(encodeURIComponent(ch)).length;
      if (bytes + size > 75) {
        out.push(current);
        current = ' ';
        bytes = 1;
      }
      current += ch;
      bytes += size;
    });
    out.push(current);
    return out.join('\r\n');
  }

  function buildIcs(ev, now) {
    var t = eventTimes(ev);
    var lines = [
      'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//SHEMA//shema.com.au//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
      'BEGIN:VEVENT',
      'UID:' + ev.id + '@shema.com.au',
      'DTSTAMP:' + utcStamp(now || new Date())
    ];
    if (t.allDay) {
      lines.push('DTSTART;VALUE=DATE:' + t.start, 'DTEND;VALUE=DATE:' + t.end);
    } else {
      lines.push('DTSTART:' + t.start, 'DTEND:' + t.end);
    }
    lines.push('SUMMARY:' + icsEscape(ev.title));
    var loc = locationText(ev.venue);
    if (loc) lines.push('LOCATION:' + icsEscape(loc));
    lines.push('DESCRIPTION:' + icsEscape(ev.description || '') + '\\n\\n' + SITE + '/#events');
    lines.push('URL:' + SITE + '/#events');
    lines.push('STATUS:' + (ev.status === 'cancelled' ? 'CANCELLED' : 'CONFIRMED'));
    lines.push('END:VEVENT', 'END:VCALENDAR');
    return lines.map(fold).join('\r\n') + '\r\n';
  }

  function googleLink(ev) {
    var t = eventTimes(ev);
    return 'https://calendar.google.com/calendar/render?action=TEMPLATE' +
      '&text=' + encodeURIComponent(ev.title) +
      '&dates=' + encodeURIComponent(t.start + '/' + t.end) +
      '&details=' + encodeURIComponent(ev.description || '') +
      '&location=' + encodeURIComponent(locationText(ev.venue)) +
      '&ctz=' + encodeURIComponent(TZ);
  }

  function jsonLd(events) {
    return events.map(function (ev) {
      var status = { upcoming: 'EventScheduled', cancelled: 'EventCancelled', postponed: 'EventPostponed' }[ev.status] || 'EventScheduled';
      var item = {
        '@context': 'https://schema.org',
        '@type': 'Event',
        name: ev.title,
        startDate: ev.start,
        eventStatus: 'https://schema.org/' + status,
        eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
        description: ev.description,
        url: SITE + '/#events',
        organizer: { '@type': 'Organization', name: 'Shepparton Malayalee Association (SHEMA) Inc.', url: SITE + '/' }
      };
      if (ev.end) item.endDate = ev.end;
      if (ev.venue) {
        item.location = {
          '@type': 'Place', name: ev.venue.name,
          address: {
            '@type': 'PostalAddress', streetAddress: ev.venue.address || undefined, addressLocality: ev.venue.suburb,
            addressRegion: ev.venue.state || 'VIC', postalCode: ev.venue.postcode || undefined, addressCountry: 'AU'
          }
        };
      }
      if (ev.image) item.image = SITE + '/' + ev.image.src.replace(/^\//, '') + '-1600.jpg';
      var tickets = (ev.links || []).filter(function (l) { return l.kind === 'tickets'; })[0];
      if (tickets) item.offers = { '@type': 'Offer', url: tickets.url };
      return item;
    });
  }

  function formatWhen(ev) {
    if (ev.datePrecision === 'year' || ev.datePrecision === 'month') return ev.start.slice(0, 4);
    var start = ev.datePrecision === 'date' ? new Date(ev.start + 'T12:00:00+10:00') : new Date(ev.start);
    var parts = {};
    new Intl.DateTimeFormat('en-AU', { timeZone: TZ, weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
      .formatToParts(start).forEach(function (p) { parts[p.type] = p.value; });
    var day = parts.weekday + ', ' + parts.day + ' ' + parts.month + ' ' + parts.year;
    if (ev.datePrecision === 'date') return day + ', All day';
    var time = new Intl.DateTimeFormat('en-AU', { timeZone: TZ, hour: 'numeric', minute: '2-digit' }).format(start)
      .replace(/\u202f|\s/g, ' ').replace(/ ?(am|pm)$/i, function (m) { return ' ' + m.trim().toLowerCase(); });
    return day + ', ' + time;
  }

  function badgeParts(ev) {
    var start = ev.datePrecision === 'date' ? new Date(ev.start + 'T12:00:00+10:00') : new Date(ev.start);
    return {
      day: new Intl.DateTimeFormat('en-AU', { timeZone: TZ, day: 'numeric' }).format(start),
      month: new Intl.DateTimeFormat('en-AU', { timeZone: TZ, month: 'short' }).format(start).toUpperCase()
    };
  }

  var api = {
    splitEvents: splitEvents, buildIcs: buildIcs, googleLink: googleLink, jsonLd: jsonLd,
    formatWhen: formatWhen, eventTimes: eventTimes, melbourneToday: melbourneToday
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
    return;
  }
  root.SHEMAEvents = api;

  /* ------------------------------------------------------------ DOM rendering */
  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      if (key === 'text') node.textContent = attrs[key];
      else node.setAttribute(key, attrs[key]);
    });
    (children || []).forEach(function (child) { if (child) node.appendChild(child); });
    return node;
  }

  function tilePicture(ev, sizes) {
    var picture = el('picture', { class: 'event-media' });
    if (ev.image) {
      var base = ev.image.src;
      picture.appendChild(el('source', { type: 'image/avif', srcset: base + '-480.avif 480w, ' + base + '-960.avif 960w', sizes: sizes }));
      picture.appendChild(el('img', {
        src: base + '-960.webp', srcset: base + '-480.webp 480w, ' + base + '-960.webp 960w', sizes: sizes,
        width: String(ev.image.width), height: String(ev.image.height), alt: ev.image.alt, loading: 'lazy', decoding: 'async'
      }));
      return picture;
    }
    var tile = TILE[ev.category];
    if (!tile) {
      picture.classList.add('event-media--plain');
      return picture;
    }
    var path = '/assets/tiles/tile-' + tile;
    picture.appendChild(el('source', { type: 'image/avif', srcset: path + '-360.avif 360w, ' + path + '-720.avif 720w', sizes: sizes }));
    picture.appendChild(el('img', {
      src: path + '-720.webp', srcset: path + '-360.webp 360w, ' + path + '-720.webp 720w', sizes: sizes,
      width: '720', height: '540', alt: '', loading: 'lazy', decoding: 'async'
    }));
    return picture;
  }

  function linkButton(link, title, extraClass) {
    var label = link.label;
    /* the visible label comes first so the accessible name contains it (WCAG 2.5.3) */
    return el('a', {
      class: 'btn btn--sm ' + (extraClass || 'btn--outline'), href: link.url, target: '_blank',
      rel: 'noopener noreferrer', 'aria-label': label + ': ' + title + ' (opens in a new tab)', text: label
    });
  }

  function pastCard(ev) {
    var actions = el('div', { class: 'event-actions' }, (ev.links || []).map(function (l) { return linkButton(l, ev.title); }));
    var body = el('div', { class: 'event-body' }, [
      el('p', { class: 'event-head' }, [
        el('span', { class: 'chip chip--' + ev.category, text: CATEGORY_LABEL[ev.category] || ev.category.toUpperCase() }),
        el('span', { class: 'event-when' }, [el('time', { datetime: ev.start, text: formatWhen(ev) })])
      ]),
      el('h3', { text: ev.title }),
      el('p', { class: 'event-desc', text: ev.description }),
      (ev.links || []).length ? actions : null
    ]);
    var card = el('article', { class: 'event-card event-memory-card reveal', id: 'event-' + ev.id, 'data-category': ev.category },
      [tilePicture(ev, '(max-width: 700px) 112px, 200px'), body]);
    return card;
  }

  function downloadIcs(ev) {
    var blob = new Blob([buildIcs(ev, new Date())], { type: 'text/calendar;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = el('a', { href: url, download: ev.id + '.ics' });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function upcomingCard(ev) {
    var badge = badgeParts(ev);
    var status = ev.status === 'cancelled' ? 'Cancelled' : ev.status === 'postponed' ? 'Postponed – new date to be announced' : '';
    var lines = [
      el('div', { class: 'event-chips' }, [
        el('span', { class: 'chip chip--' + ev.category, text: CATEGORY_LABEL[ev.category] || ev.category.toUpperCase() }),
        status ? el('span', { class: 'chip chip--status', text: status }) : null
      ]),
      el('h3', { text: ev.title }),
      el('p', { class: 'event-when' }, [el('time', { datetime: ev.start, text: formatWhen(ev) })])
    ];
    if (ev.venue) lines.push(el('p', { class: 'event-venue', text: locationText(ev.venue) }));
    lines.push(el('p', { class: 'event-desc', text: ev.description }));
    var actions = el('div', { class: 'event-actions' });
    if (!status) {
      var ics = el('button', { type: 'button', class: 'btn btn--sm btn--outline', text: 'Add to calendar', 'aria-label': 'Add to calendar: ' + ev.title + ' (.ics file)' });
      ics.addEventListener('click', function () { downloadIcs(ev); });
      actions.appendChild(ics);
      actions.appendChild(el('a', {
        class: 'btn btn--sm btn--outline', href: googleLink(ev), target: '_blank', rel: 'noopener noreferrer',
        text: 'Google Calendar', 'aria-label': 'Google Calendar: ' + ev.title + ' (opens in a new tab)'
      }));
    }
    (ev.links || []).forEach(function (l) {
      if (l.kind === 'tickets' || l.kind === 'details') actions.appendChild(linkButton(l, ev.title, 'btn--green'));
    });
    lines.push(actions);
    var media = tilePicture(ev, '(max-width: 700px) 100vw, 440px');
    var badgeEl = el('div', { class: 'date-badge', 'aria-hidden': 'true' }, [
      el('span', { class: 'date-badge-day', text: badge.day }), el('span', { class: 'date-badge-month', text: badge.month })
    ]);
    return el('article', { class: 'upcoming-card', id: 'event-' + ev.id }, [
      el('div', { class: 'upcoming-media' }, [media, badgeEl]), el('div', { class: 'event-body' }, lines)
    ]);
  }

  function render(data) {
    var lists = splitEvents(data, new Date());
    var upcomingWrap = document.getElementById('upcomingList');
    var pastWrap = document.getElementById('pastList');
    if (upcomingWrap && lists.upcoming.length) {
      upcomingWrap.replaceChildren.apply(upcomingWrap, lists.upcoming.map(upcomingCard));
      var ld = document.createElement('script');
      ld.type = 'application/ld+json';
      ld.textContent = JSON.stringify(jsonLd(lists.upcoming));
      document.head.appendChild(ld);
    }
    if (pastWrap && lists.past.length) {
      pastWrap.replaceChildren.apply(pastWrap, lists.past.map(pastCard));
    }
  }

  function init() {
    if (!document.getElementById('upcomingList')) return;
    fetch('/events.json', { credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(render)
      .catch(function (err) { console.warn('events.json not loaded; static event cards kept.', err); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})(typeof window !== 'undefined' ? window : globalThis);
