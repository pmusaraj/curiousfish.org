(() => {
  // Local calendar dates, normalized to avoid daylight-saving time differences.
  function activityLabel(timestamp, now = new Date()) {
    const calendarDay = (date) => Date.UTC(date.getFullYear(), date.getMonth(), date.getDate());
    const days = Math.max(0, Math.round((calendarDay(now) - calendarDay(timestamp)) / 86400000));
    if (days === 0) return "today";
    if (days === 1) return "yesterday";
    return `${days} days ago`;
  }

  function updateActivity() {
    document.querySelectorAll(".socials time[datetime]").forEach((element) => {
      const timestamp = new Date(element.dateTime);
      if (Number.isNaN(timestamp.getTime())) return;
      const label = activityLabel(timestamp);
      element.textContent = label;
      element.setAttribute("aria-label", `Last activity: ${label}`);
    });
  }
  updateActivity();
  window.setInterval(updateActivity, 60000);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) updateActivity();
  });
})();
