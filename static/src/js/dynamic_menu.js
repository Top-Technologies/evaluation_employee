/** @odoo-module **/

import { browser } from "@web/core/browser/browser";

/**
 * Menu visibility:
 * - Every 4 months
 * - Visible for 10 days only
 */
browser.setInterval(() => {
    const menuXmlId = "evaluation_employee.evaluation_model_menu_action";

    // 🔴 SET YOUR FIRST EVALUATION START DATE HERE (ONCE)
    const cycleStartDate = new Date(2026, 0, 28); // Jan 1, 2025

    const now = new Date();

    // Total months passed since start
    const totalMonths =
        (now.getFullYear() - cycleStartDate.getFullYear()) * 12 +
        (now.getMonth() - cycleStartDate.getMonth());

    // Position inside 4-month cycle (0–3)
    const cyclePosition = totalMonths % 4;

    let isVisible = false;

    // Only first month of cycle can be visible
    if (cyclePosition === 0) {
        const cycleMonthStart = new Date(
            now.getFullYear(),
            now.getMonth(),
            cycleStartDate.getDate()
        );

        const daysPassed = Math.floor(
            (now - cycleMonthStart) / (1000 * 60 * 60 * 24)
        );

        // Visible ONLY for first 10 days
        isVisible = daysPassed >= 0 && daysPassed < 10;
    }

    const menuElements = document.querySelectorAll(
        `[data-menu-xmlid="${menuXmlId}"]`
    );

    menuElements.forEach(el => {
        const container = el.closest("li") || el;

        container.classList.toggle("d-none", !isVisible);
        if (isVisible) {
            container.style.display = "";
        }
    });

}, 60 * 1000); // check every minute
