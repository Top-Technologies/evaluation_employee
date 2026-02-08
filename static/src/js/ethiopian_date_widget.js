/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useRef, onMounted, onWillUpdateProps, useState } from "@odoo/owl";
import { EthiopicDate } from "./ethiopian_date.min";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { deserializeDate } from "@web/core/l10n/dates";

export class EthiopianDateWidget extends Component {
    static template = "evaluation_employee.EthiopianDateWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.inputRef = useRef("input");

        this.state = useState({
            showPicker: false,
            // View state for the picker (which month/year is currently shown)
            viewYear: 2016,
            viewMonth: 1,
        });

        this.amharicMonths = [
            'መስከረም', 'ጥቅምት', 'ኅዳር', 'ታኅሣሥ',
            'ጥር', 'የካቲት', 'መጋቢት', 'ሚያዝያ',
            'ግንቦት', 'ሰኔ', 'ሐምሌ', 'ነሐሴ', 'ጳጉሜን'
        ];

        this.weekDays = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

        onMounted(() => {
            this.syncFromRecord(this.props.record.data[this.props.name]);
        });

        onWillUpdateProps((nextProps) => {
            this.syncFromRecord(nextProps.record.data[nextProps.name]);
        });
    }

    syncFromRecord(dateValue) {
        if (!dateValue) {
            if (this.inputRef.el) this.inputRef.el.value = "";
            return;
        }

        let date;
        // Handle Luxon DateTime objects (standard in Odoo 18)
        if (typeof dateValue === 'object' && dateValue.toJSDate) {
            date = dateValue.toJSDate();
        } else if (typeof dateValue === 'string') {
            // Fallback for ISO strings
            date = new Date(dateValue);
        } else {
            return;
        }

        if (!isNaN(date)) {
            const eth = EthiopicDate.fromGregorian(date);
            if (this.inputRef.el) {
                this.inputRef.el.value = `${eth.day} ${this.amharicMonths[eth.month - 1]} ${eth.year}`;
            }

            // Sync picker view to selected date
            this.state.viewYear = eth.year;
            this.state.viewMonth = eth.month;
        }
    }

    togglePicker() {
        this.state.showPicker = !this.state.showPicker;
    }

    changeMonth(delta) {
        let newMonth = this.state.viewMonth + delta;
        let newYear = this.state.viewYear;

        if (newMonth > 13) {
            newMonth = 1;
            newYear++;
        } else if (newMonth < 1) {
            newMonth = 13;
            newYear--;
        }

        this.state.viewMonth = newMonth;
        this.state.viewYear = newYear;
    }

    changeYear(delta) {
        this.state.viewYear += delta;
    }

    selectDate(day) {
        // Convert selected Ethiopic date to Gregorian and save
        const gregDate = EthiopicDate.toGregorian(this.state.viewYear, this.state.viewMonth, day);
        const isoDate = gregDate.toISOString().slice(0, 10);

        // Optimistic UI update
        if (this.inputRef.el) {
            this.inputRef.el.value = `${day} ${this.amharicMonths[this.state.viewMonth - 1]} ${this.state.viewYear}`;
        }

        // Deserialize to Luxon (or whatever Odoo expects) before updating
        this.props.record.update({ [this.props.name]: deserializeDate(isoDate) });
        this.state.showPicker = false;
    }

    get calendarRows() {
        const year = this.state.viewYear;
        const month = this.state.viewMonth;

        const daysInMonth = EthiopicDate.getDaysInMonth(year, month);
        const firstDayGreg = EthiopicDate.toGregorian(year, month, 1);
        const startWeekday = firstDayGreg.getDay(); // 0=Sun, 1=Mon...

        let rows = [];
        let currentRow = [];

        for (let i = 0; i < startWeekday; i++) {
            currentRow.push(null);
        }

        for (let day = 1; day <= daysInMonth; day++) {
            currentRow.push(day);
            if (currentRow.length === 7) {
                rows.push(currentRow);
                currentRow = [];
            }
        }

        if (currentRow.length > 0) {
            while (currentRow.length < 7) {
                currentRow.push(null);
            }
            rows.push(currentRow);
        }

        return rows;
    }

    onChange(ev) {
        const value = ev.target.value;
        if (!value) {
            this.props.record.update({ [this.props.name]: false });
            return;
        }

        const parts = value.trim().split(/[\s/-]+/);
        if (parts.length === 3) {
            let day = parseInt(parts[0]);
            let month = parts[1];
            let year = parseInt(parts[2]);

            let monthIndex = this.amharicMonths.indexOf(month);
            if (monthIndex !== -1) month = monthIndex + 1;
            else month = parseInt(month);

            if (!isNaN(day) && !isNaN(month) && !isNaN(year)) {
                const gregDate = EthiopicDate.toGregorian(year, month, day);
                if (!isNaN(gregDate)) {
                    const isoDate = gregDate.toISOString().slice(0, 10);
                    this.props.record.update({ [this.props.name]: deserializeDate(isoDate) });
                }
            }
        }
    }
}

// Formatter for tree/list view display
function formatEthiopianDate(value) {
    if (!value) return "";

    const amharicMonths = [
        'መስከረም', 'ጥቅምት', 'ኅዳር', 'ታኅሣሥ',
        'ጥር', 'የካቲት', 'መጋቢት', 'ሚያዝያ',
        'ግንቦት', 'ሰኔ', 'ሐምሌ', 'ነሐሴ', 'ጳጉሜን'
    ];

    let date;
    // Handle Luxon DateTime objects
    if (typeof value === 'object' && value.toJSDate) {
        date = value.toJSDate();
    } else if (typeof value === 'string') {
        date = new Date(value);
    } else {
        return "";
    }

    if (isNaN(date)) return "";

    const eth = EthiopicDate.fromGregorian(date);
    return `${eth.day} ${amharicMonths[eth.month - 1]} ${eth.year}`;
}

export const ethiopianDateWidget = {
    component: EthiopianDateWidget,
    displayName: "Ethiopian Date",
    supportedTypes: ["date", "datetime"],
    extractProps: ({ attrs, field }) => {
        return {};
    },
};

registry.category("fields").add("ethiopian_date", ethiopianDateWidget);
