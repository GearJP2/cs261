(function () {
  "use strict";

  const API = "/api/v1";

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function apiMessage(payload, fallback) {
    if (!payload || !payload.error) return fallback;
    const fields = payload.error.fields || {};
    const fieldMessages = Object.values(fields).filter(Boolean);
    return [payload.error.message, ...fieldMessages].filter(Boolean).join(" ");
  }

  async function csrfToken() {
    const response = await fetch(`${API}/auth/csrf`, { credentials: "same-origin" });
    const payload = await response.json();
    if (!response.ok) throw new Error(apiMessage(payload, "ไม่สามารถเตรียมการเข้าสู่ระบบได้"));
    return payload.data.csrf_token;
  }

  async function request(path, options) {
    const settings = Object.assign({ credentials: "same-origin" }, options || {});
    settings.headers = Object.assign({ Accept: "application/json" }, settings.headers || {});
    if (settings.method && !["GET", "HEAD"].includes(settings.method)) {
      settings.headers["X-CSRFToken"] = await csrfToken();
      settings.headers["Content-Type"] = "application/json";
    }
    const response = await fetch(`${API}${path}`, settings);
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const error = new Error(apiMessage(payload, "เกิดข้อผิดพลาด กรุณาลองใหม่"));
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return payload.data;
  }

  async function currentUser() {
    try { return await request("/me"); } catch (error) { return null; }
  }

  function initials(name) {
    return (name || "U").trim().slice(0, 1).toUpperCase();
  }

  async function initNavigation() {
    const user = await currentUser();
    const avatar = document.querySelector(".nv-avatar");
    const login = document.querySelector("[data-login-link]");
    const profile = document.querySelector("[data-profile-link]");
    const logout = document.querySelector("[data-logout-button]");
    if (!user) return null;
    if (avatar) avatar.textContent = initials(user.display_name);
    if (login) login.hidden = true;
    if (profile) { profile.href = `/users/${user.id}/`; profile.hidden = false; }
    if (logout) logout.hidden = false;
    return user;
  }

  document.addEventListener("click", async function (event) {
    const button = event.target.closest("[data-logout-button]");
    if (!button) return;
    event.preventDefault();
    button.disabled = true;
    try { await request("/auth/logout", { method: "POST", body: "{}" }); window.location.assign("/"); }
    catch (error) { button.disabled = false; alert(error.message); }
  });

  function setError(container, message) {
    container.hidden = !message;
    container.textContent = message || "";
  }

  async function initLogin() {
    const form = document.querySelector("[data-login-form]");
    if (!form) return;
    if (await currentUser()) { window.location.replace("/"); return; }
    const errorBox = form.querySelector("[data-form-error]");
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      setError(errorBox, "");
      const button = form.querySelector("button[type=submit]");
      const username = form.elements.username.value.trim();
      const password = form.elements.password.value;
      if (!username || !password) { setError(errorBox, "กรุณากรอก Username และ Password"); return; }
      button.disabled = true;
      try {
        await request("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
        window.location.assign("/");
      } catch (error) { setError(errorBox, error.message); button.disabled = false; }
    });
  }

  function formatDateTime(iso) {
    return new Intl.DateTimeFormat("th-TH", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Bangkok" }).format(new Date(iso));
  }

  function partyCard(party, catalog) {
    const card = element("article", "hp-card");
    const top = element("div", "hp-card-top");
    const sport = catalog.sports.get(party.sport_id) || "กีฬา";
    top.append(element("span", "hp-tag", sport), element("span", "hp-open", "● เปิดรับอยู่"));
    const title = element("h3", "", party.title);
    const venue = catalog.venues.get(`${party.sport_id}:${party.venue_id}`) || "สนามกีฬา";
    const host = element("div", "hp-host");
    host.append(element("span", "", `ชวนโดย ${party.host.display_name}`), element("span", "", `${party.member_count}/${party.capacity} คน`));
    const foot = element("div", "hp-card-foot");
    foot.append(element("span", "", `เหลือ ${party.remaining_slots} ที่`));
    const link = element("a", "hp-join", "ดูรายละเอียด");
    link.href = `/parties/${party.id}/`;
    foot.append(link);
    card.append(top, title, element("div", "hp-row", `📍 ${venue}`), element("div", "hp-row", `📅 ${formatDateTime(party.starts_at)}`), host, foot);
    return card;
  }

  async function catalogForParties(parties) {
    const sports = await request("/sports");
    const sportNames = new Map(sports.map((sport) => [sport.id, sport.name]));
    const neededSports = [...new Set(parties.map((party) => party.sport_id))];
    const responses = await Promise.all(neededSports.map(async (sportId) => [sportId, await request(`/venues?sport_id=${sportId}`)]));
    const venues = new Map();
    responses.forEach(([sportId, response]) => response.forEach((venue) => venues.set(`${sportId}:${venue.id}`, venue.name)));
    return { sports: sportNames, venues };
  }

  async function initHome() {
    const section = document.querySelector("[data-home-parties]");
    if (!section) return;
    const message = section.querySelector("[data-home-message]");
    const list = section.querySelector("[data-party-list]");
    const user = await currentUser();
    if (!user) {
      message.textContent = "เข้าสู่ระบบด้วยบัญชีมหาวิทยาลัยเพื่อดูและเข้าร่วมปาร์ตี้";
      return;
    }
    try {
      const parties = await request("/parties");
      if (!parties.length) { message.textContent = "ยังไม่มีปาร์ตี้ที่กำลังเปิดรับ ลองสร้างปาร์ตี้แรกได้เลย"; return; }
      const catalog = await catalogForParties(parties);
      list.replaceChildren(...parties.map((party) => partyCard(party, catalog)));
      list.hidden = false;
      message.hidden = true;
    } catch (error) { message.textContent = error.message; }
  }

  function bangkokDateTimeParts(iso) {
    const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Bangkok", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(iso));
    const value = (type) => parts.find((part) => part.type === type).value;
    return { date: `${value("year")}-${value("month")}-${value("day")}`, time: `${value("hour")}:${value("minute")}` };
  }

  function formatHours(intervals) {
    const days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"];
    if (!intervals.length) return "สนามนี้ยังไม่มีเวลาเปิดบริการ";
    return intervals.map((entry) => `${days[entry.weekday]} ${entry.opens_at.slice(0, 5)}–${entry.closes_at.slice(0, 5)} น.`).join(" · ");
  }

  function localScheduleValid(form, intervals) {
    const date = form.elements.date.value;
    const start = form.elements.start_time.value;
    const end = form.elements.end_time.value;
    if (!date || !start || !end || !intervals) return { valid: true, message: "" };
    if (end <= start) return { valid: false, message: "เวลาสิ้นสุดต้องอยู่หลังเวลาเริ่ม" };
    const weekday = (new Date(`${date}T12:00:00+07:00`).getUTCDay() + 6) % 7;
    const valid = intervals.some((entry) => entry.weekday === weekday && entry.opens_at.slice(0, 5) <= start && end <= entry.closes_at.slice(0, 5));
    return valid ? { valid: true, message: "ช่วงเวลาที่เลือกอยู่ในเวลาเปิดบริการ" } : { valid: false, message: "ช่วงเวลาที่เลือกอยู่นอกเวลาเปิดสนาม" };
  }

  async function initPartyForm() {
    const page = document.querySelector("[data-party-form-page]");
    if (!page) return;
    if (!await currentUser()) { window.location.replace("/login/"); return; }
    const form = page.querySelector("[data-party-form]");
    const mode = page.dataset.mode;
    const partyId = page.dataset.partyId;
    const sportSelect = form.querySelector("[data-sport-select]");
    const venueSelect = form.querySelector("[data-venue-select]");
    const hoursBox = form.querySelector("[data-hours-message]");
    const errorBox = form.querySelector("[data-form-error]");
    let intervals = null;

    function renderScheduleCheck() {
      const check = localScheduleValid(form, intervals);
      if (intervals && form.elements.date.value && form.elements.start_time.value && form.elements.end_time.value) {
        hoursBox.textContent = check.message;
        hoursBox.classList.toggle("is-error", !check.valid);
      }
      return check;
    }
    async function loadVenues(selectedVenue) {
      venueSelect.replaceChildren(new Option("เลือกสนาม", ""));
      venueSelect.disabled = true; intervals = null;
      if (!sportSelect.value) { venueSelect.options[0].text = "เลือกกีฬาก่อน"; hoursBox.textContent = "เลือกสนามเพื่อดูเวลาเปิดบริการ"; return; }
      try {
        const venues = await request(`/venues?sport_id=${sportSelect.value}`);
        venues.forEach((venue) => venueSelect.add(new Option(`${venue.name} — ${venue.location_text}`, venue.id)));
        venueSelect.disabled = false;
        if (selectedVenue) { venueSelect.value = String(selectedVenue); await loadHours(); }
      } catch (error) { hoursBox.textContent = error.message; hoursBox.classList.add("is-error"); }
    }
    async function loadHours() {
      intervals = null;
      if (!venueSelect.value) { hoursBox.textContent = "เลือกสนามเพื่อดูเวลาเปิดบริการ"; return; }
      try {
        const hours = await request(`/venues/${venueSelect.value}/opening-hours`);
        intervals = hours.intervals;
        hoursBox.textContent = formatHours(intervals);
        hoursBox.classList.remove("is-error");
        renderScheduleCheck();
      } catch (error) { hoursBox.textContent = error.message; hoursBox.classList.add("is-error"); }
    }
    sportSelect.addEventListener("change", () => loadVenues());
    venueSelect.addEventListener("change", loadHours);
    [form.elements.date, form.elements.start_time, form.elements.end_time].forEach((input) => input.addEventListener("change", renderScheduleCheck));
    try {
      const sports = await request("/sports");
      sports.forEach((sport) => sportSelect.add(new Option(sport.name, sport.id)));
      if (mode === "edit") {
        const party = await request(`/parties/${partyId}`);
        if (!party.is_host) { window.location.replace(`/parties/${partyId}/`); return; }
        form.elements.title.value = party.title; form.elements.description.value = party.description;
        form.elements.capacity.value = party.capacity; sportSelect.value = String(party.sport_id);
        const starts = bangkokDateTimeParts(party.starts_at); const ends = bangkokDateTimeParts(party.ends_at);
        form.elements.date.value = starts.date; form.elements.start_time.value = starts.time; form.elements.end_time.value = ends.time;
        await loadVenues(party.venue_id);
      }
    } catch (error) { setError(errorBox, error.message); return; }
    form.addEventListener("submit", async function (event) {
      event.preventDefault(); setError(errorBox, "");
      const check = renderScheduleCheck();
      if (!form.reportValidity() || !check.valid) { if (!check.valid) setError(errorBox, check.message); return; }
      const date = form.elements.date.value;
      const payload = { title: form.elements.title.value, description: form.elements.description.value, sport_id: Number(sportSelect.value), venue_id: Number(venueSelect.value), starts_at: `${date}T${form.elements.start_time.value}:00+07:00`, ends_at: `${date}T${form.elements.end_time.value}:00+07:00`, capacity: Number(form.elements.capacity.value) };
      const submit = form.querySelector("[data-submit-party]"); submit.disabled = true;
      try {
        const party = await request(mode === "edit" ? `/parties/${partyId}` : "/parties", { method: mode === "edit" ? "PATCH" : "POST", body: JSON.stringify(payload) });
        window.location.assign(`/parties/${party.id}/`);
      } catch (error) { setError(errorBox, error.message); submit.disabled = false; }
    });
  }

  function detailRow(label, value) { const row = element("div"); row.append(element("strong", "", `${label}: `), document.createTextNode(value)); return row; }

  async function initPartyDetail() {
    const root = document.querySelector("[data-party-detail]");
    if (!root) return;
    if (!await currentUser()) { window.location.replace("/login/"); return; }
    const partyId = root.dataset.partyId;
    try {
      const party = await request(`/parties/${partyId}`);
      const [sports, venues] = await Promise.all([request("/sports"), request(`/venues?sport_id=${party.sport_id}`)]);
      const sport = sports.find((item) => item.id === party.sport_id); const venue = venues.find((item) => item.id === party.venue_id);
      const layout = element("div", "detail-layout"); const main = element("article", "detail-card");
      main.append(element("div", "detail-status", party.state === "Open" ? "● เปิดรับอยู่" : party.state), element("h1", "", party.title), element("p", "detail-description", party.description || "ไม่มีรายละเอียดเพิ่มเติม"));
      const meta = element("div", "detail-meta");
      meta.append(detailRow("กีฬา", sport ? sport.name : "-"), detailRow("สนาม", venue ? `${venue.name} — ${venue.location_text}` : "-"), detailRow("วันและเวลา", `${formatDateTime(party.starts_at)} – ${new Intl.DateTimeFormat("th-TH", { timeStyle: "short", timeZone: "Asia/Bangkok" }).format(new Date(party.ends_at))}`));
      main.append(meta);
      const side = element("aside", "detail-side"); const slots = element("section", "detail-card");
      slots.append(element("div", "", "ผู้เล่นที่เข้าร่วม"), element("div", "detail-number", `${party.member_count}/${party.capacity}`), element("div", "", `เหลือ ${party.remaining_slots} ที่`)); side.append(slots);
      const host = element("section", "detail-card"); host.append(element("div", "", "จัดโดย")); const profile = element("a", "detail-host", party.host.display_name); profile.href = `/users/${party.host.id}/`; host.append(profile); side.append(host);
      const actions = element("section", "detail-card detail-actions");
      if (party.is_host) {
        const edit = element("a", "app-primary", "แก้ไขปาร์ตี้"); edit.href = `/parties/${party.id}/edit/`;
        const cancel = element("button", "app-secondary app-danger", "ยกเลิกปาร์ตี้");
        cancel.addEventListener("click", async () => { if (!window.confirm("ต้องการยกเลิกปาร์ตี้นี้หรือไม่?")) return; cancel.disabled = true; try { await request(`/parties/${party.id}/cancel`, { method: "POST", body: "{}" }); window.location.reload(); } catch (error) { cancel.disabled = false; alert(error.message); } });
        actions.append(edit, cancel);
      } else if (party.is_member) actions.append(element("div", "app-success", "คุณเป็นสมาชิกของปาร์ตี้นี้แล้ว"));
      else if (party.state === "Open") {
        const existing = await request(`/parties/${party.id}/join-requests/me`);
        if (existing && existing.status === "Pending") actions.append(element("div", "app-success", "ส่งคำขอเข้าร่วมแล้ว กำลังรอการตอบรับ"));
        else {
          const join = element("button", "app-primary", "ขอเข้าร่วม");
          join.addEventListener("click", async () => { join.disabled = true; try { await request(`/parties/${party.id}/join-requests`, { method: "POST", body: "{}" }); window.location.reload(); } catch (error) { join.disabled = false; alert(error.message); } });
          actions.append(join);
        }
      } else actions.append(element("div", "app-message", "ปาร์ตี้นี้ไม่เปิดรับคำขอในขณะนี้"));
      side.append(actions); layout.append(main, side); root.querySelector(".app-message").replaceWith(layout);
    } catch (error) { const message = root.querySelector(".app-message"); message.textContent = error.message; }
  }

  document.addEventListener("DOMContentLoaded", async function () {
    const navReady = initNavigation();
    await Promise.all([navReady, initLogin(), initHome(), initPartyForm(), initPartyDetail()]);
  });
})();
