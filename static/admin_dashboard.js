(function () {
    const state = {
        reportsPage: 1,
        selectedReportId: null,
        reportPagination: null,
        charts: {},
        map: null,
        mapLayer: null,
        reportFilters: {
            search: "",
            hazard_type: "",
            severity: "",
            status: "",
            start_date: "",
            end_date: "",
        },
        mapFilters: {
            hazard_type: "",
            severity: "",
            status: "pending",
            start_date: "",
            end_date: "",
        },
    };

    const severityColors = {
        critical: "#dc2626",
        high: "#f97316",
        medium: "#2563eb",
        low: "#16a34a",
    };

    const statusLabelMap = {
        pending: "Pending",
        acknowledged: "Acknowledged",
        "in progress": "In Progress",
        resolved: "Resolved",
    };

    document.addEventListener("DOMContentLoaded", () => {
        bindNavigation();
        bindFilters();
        bindDetailForm();
        setFilterOptions();
        initializeMap();
        initializeDashboard();
    });

    function bindNavigation() {
        const buttons = document.querySelectorAll(".nav-link");
        const sections = document.querySelectorAll(".dashboard-section");

        buttons.forEach((button) => {
            button.addEventListener("click", () => {
                const target = button.dataset.section;
                buttons.forEach((item) => item.classList.toggle("active", item === button));
                sections.forEach((section) => {
                    section.classList.toggle("active", section.id === target);
                });

                if (target === "map-view" && state.map) {
                    setTimeout(() => state.map.invalidateSize(), 80);
                }
            });
        });
    }

    function bindFilters() {
        const reportFilterButton = document.getElementById("reportFilterButton");
        const mapFilterButton = document.getElementById("mapApplyFilters");
        const prevPage = document.getElementById("prevPage");
        const nextPage = document.getElementById("nextPage");

        reportFilterButton.addEventListener("click", () => {
            state.reportsPage = 1;
            syncReportFilters();
            loadReports();
        });

        mapFilterButton.addEventListener("click", () => {
            syncMapFilters();
            loadMapPins();
        });

        prevPage.addEventListener("click", () => {
            if (state.reportsPage > 1) {
                state.reportsPage -= 1;
                loadReports();
            }
        });

        nextPage.addEventListener("click", () => {
            if (!state.reportPagination || state.reportsPage >= state.reportPagination.total_pages) {
                return;
            }
            state.reportsPage += 1;
            loadReports();
        });
    }

    function bindDetailForm() {
        const form = document.getElementById("detailForm");
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (!state.selectedReportId) {
                return;
            }

            const payload = {
                status: document.getElementById("detailStatus").value,
                assigned_team: document.getElementById("detailTeam").value,
                notes: document.getElementById("detailNotes").value,
                updated_by: "Admin Authority",
            };

            const response = await fetch(`/api/detections/${state.selectedReportId}/status`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await response.json();
            const statusMessage = document.getElementById("detailStatusMessage");
            statusMessage.hidden = false;

            if (!response.ok) {
                statusMessage.textContent = data.error || "Unable to update report.";
                statusMessage.className = "status error";
                return;
            }

            statusMessage.textContent = data.message;
            statusMessage.className = "status success";

            await Promise.all([
                loadOverview(),
                loadReports(),
                loadDetail(state.selectedReportId),
                loadAnalytics(),
                loadMapPins(),
            ]);
        });
    }

    function setFilterOptions() {
        const hazardOptions = [
            "",
            "Pothole",
            "Longitudinal Crack",
            "Alligator Crack",
            "Transverse Crack",
            "Edge Break",
            "Rut",
            "Depression",
        ];
        const severityOptions = ["", "critical", "high", "medium", "low"];
        const statusOptions = ["", "pending", "acknowledged", "in progress", "resolved"];

        fillSelect("mapHazardFilter", hazardOptions, "All hazard types");
        fillSelect("reportHazardFilter", hazardOptions, "All hazard types");
        fillSelect("mapSeverityFilter", severityOptions, "All severities");
        fillSelect("reportSeverityFilter", severityOptions, "All severities");
        fillSelect("mapStatusFilter", statusOptions, "All statuses");
        fillSelect("reportStatusFilter", statusOptions, "All statuses");

        document.getElementById("mapStatusFilter").value = "pending";
    }

    function fillSelect(id, values, defaultLabel) {
        const select = document.getElementById(id);
        select.innerHTML = "";
        values.forEach((value, index) => {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = index === 0 ? defaultLabel : formatFilterLabel(value);
            select.appendChild(option);
        });
    }

    function formatFilterLabel(value) {
        if (!value) {
            return "All";
        }
        return value
            .split(" ")
            .map((item) => item.charAt(0).toUpperCase() + item.slice(1))
            .join(" ");
    }

    async function initializeDashboard() {
        await Promise.all([
            loadOverview(),
            loadReports(),
            loadAnalytics(),
            loadMapPins(),
        ]);
    }

    async function loadOverview() {
        const [summary, trend, hazard, priority] = await Promise.all([
            fetchJson("/api/dashboard/summary"),
            fetchJson("/api/dashboard/trend?days=7"),
            fetchJson("/api/dashboard/by-hazard"),
            fetchJson("/api/dashboard/priority-queue"),
        ]);

        document.getElementById("metric-total").textContent = summary.total_detections;
        document.getElementById("metric-pending").textContent = summary.pending_repairs;
        document.getElementById("metric-critical").textContent = summary.critical_unresolved;
        document.getElementById("metric-today").textContent = summary.reported_today;

        renderBarChart("trendChart", {
            labels: trend.labels,
            datasets: [
                {
                    label: "Detections",
                    data: trend.detections,
                    backgroundColor: "#f97316",
                    borderRadius: 10,
                },
                {
                    label: "Resolved",
                    data: trend.resolved,
                    backgroundColor: "#16a34a",
                    borderRadius: 10,
                },
            ],
        });

        renderBarChart("hazardChart", {
            labels: hazard.items.map((item) => item.label),
            datasets: [
                {
                    label: "Count",
                    data: hazard.items.map((item) => item.count),
                    backgroundColor: "#2563eb",
                    borderRadius: 10,
                },
            ],
        }, true);

        renderPriorityTable(priority.items);
    }

    async function loadReports() {
        syncReportFilters();
        const params = new URLSearchParams({
            page: state.reportsPage,
            per_page: 20,
        });

        Object.entries(state.reportFilters).forEach(([key, value]) => {
            if (value) {
                params.set(key, value);
            }
        });

        const data = await fetchJson(`/api/detections/?${params.toString()}`);
        state.reportPagination = data.pagination;
        renderReportsTable(data.items);
        updatePagination();

        if (!state.selectedReportId && data.items.length) {
            loadDetail(data.items[0].id);
        }
    }

    async function loadDetail(id) {
        const data = await fetchJson(`/api/detections/${id}`);
        state.selectedReportId = data.id;

        document.getElementById("detailImage").src = data.image_url;
        document.getElementById("detailIdLabel").textContent = `Report #${data.id}`;
        document.getElementById("detailInfo").innerHTML = [
            ["Hazard type", data.hazard_type],
            ["GPS coordinates", `${data.lat.toFixed(4)}, ${data.lng.toFixed(4)}`],
            ["Address", data.address],
            ["Confidence score", `${Math.round(data.confidence * 100)}%`],
            ["Detected at", formatDateTime(data.reported_at)],
            ["Vehicle or device ID", data.device_id],
        ]
            .map(([label, value]) => `<div><span>${label}</span><strong>${value}</strong></div>`)
            .join("");

        document.getElementById("detailStatus").value = data.status;
        document.getElementById("detailTeam").value = data.assigned_team || "";
        document.getElementById("detailNotes").value = data.notes || "";
        document.getElementById("detailStatusMessage").hidden = true;

        document.getElementById("activityTimeline").innerHTML = data.activity_log
            .slice()
            .reverse()
            .map((entry) => `
                <div class="timeline-item">
                    <span class="timeline-dot ${classifyStatus(entry.status)}"></span>
                    <div>
                        <strong>${formatFilterLabel(entry.status)}</strong>
                        <p>${entry.updated_by} • ${formatDateTime(entry.timestamp)}</p>
                        <span>${entry.note}</span>
                    </div>
                </div>
            `)
            .join("");
    }

    async function loadAnalytics() {
        const [trend30, severity, hazard, hotspots, allRecords] = await Promise.all([
            fetchJson("/api/dashboard/trend?days=30"),
            fetchJson("/api/dashboard/by-severity"),
            fetchJson("/api/dashboard/by-hazard"),
            fetchJson("/api/dashboard/hotspots"),
            fetchJson("/api/detections/?page=1&per_page=50"),
        ]);

        renderLineChart("thirtyDayTrendChart", trend30.labels, trend30.detections);
        renderDoughnutChart("severityChart", severity.items);
        renderBarChart("hazardBreakdownChart", {
            labels: hazard.items.map((item) => item.label),
            datasets: [
                {
                    label: "Hazards",
                    data: hazard.items.map((item) => item.count),
                    backgroundColor: "#0f766e",
                    borderRadius: 10,
                },
            ],
        });

        document.getElementById("hotspotsTableBody").innerHTML = hotspots.items
            .map((item) => `
                <tr>
                    <td>${item.location}</td>
                    <td>${item.lat.toFixed(4)}</td>
                    <td>${item.lng.toFixed(4)}</td>
                    <td>${item.count}</td>
                    <td><span class="badge ${classifySeverity(item.worst_severity)}">${formatFilterLabel(item.worst_severity)}</span></td>
                </tr>
            `)
            .join("");

        const resolvedItems = allRecords.items.filter((item) => item.resolved_at);
        let averageDays = 0;
        if (resolvedItems.length) {
            averageDays =
                resolvedItems.reduce((total, item) => {
                    const reported = new Date(item.reported_at);
                    const resolved = new Date(item.resolved_at);
                    return total + (resolved - reported) / 86400000;
                }, 0) / resolvedItems.length;
        }
        document.getElementById("averageResolution").textContent = `${averageDays.toFixed(2)} days`;
    }

    async function loadMapPins() {
        syncMapFilters();
        const params = new URLSearchParams();
        Object.entries(state.mapFilters).forEach(([key, value]) => {
            if (value) {
                params.set(key, value);
            }
        });

        const data = await fetchJson(`/api/detections/?${params.toString()}`);
        renderMapMarkers(data.items.filter((item) => item.status !== "resolved"));
    }

    function initializeMap() {
        state.map = L.map("hazardMap").setView([28.4595, 77.0266], 11);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors",
        }).addTo(state.map);
        state.mapLayer = L.layerGroup().addTo(state.map);
    }

    function renderMapMarkers(items) {
        state.mapLayer.clearLayers();
        if (!items.length) {
            return;
        }

        const bounds = [];
        items.forEach((item) => {
            const icon = L.divIcon({
                className: "severity-pin",
                html: `<span style="background:${severityColors[item.severity] || "#2563eb"}"></span>`,
                iconSize: [18, 18],
                iconAnchor: [9, 9],
            });

            const marker = L.marker([item.lat, item.lng], { icon });
            marker.bindPopup(`
                <div class="map-popup">
                    <img src="${item.image_url}" alt="${item.hazard_type}">
                    <strong>${item.hazard_type}</strong>
                    <p>${item.location}</p>
                    <p>${formatDateTime(item.reported_at)}</p>
                    <span class="badge ${classifyStatus(item.status)}">${statusLabelMap[item.status]}</span>
                </div>
            `);
            marker.addTo(state.mapLayer);
            bounds.push([item.lat, item.lng]);
        });

        state.map.fitBounds(bounds, { padding: [30, 30] });
    }

    function renderPriorityTable(items) {
        document.getElementById("priorityTableBody").innerHTML = items
            .map((item) => `
                <tr>
                    <td>${item.hazard_type}</td>
                    <td>${item.location}</td>
                    <td><span class="badge ${classifySeverity(item.severity)}">${formatFilterLabel(item.severity)}</span></td>
                    <td>${Math.round(item.confidence * 100)}%</td>
                    <td>${formatDateTime(item.reported_at)}</td>
                    <td><span class="badge ${classifyStatus(item.status)}">${statusLabelMap[item.status]}</span></td>
                </tr>
            `)
            .join("");
    }

    function renderReportsTable(items) {
        document.getElementById("reportsTableBody").innerHTML = items
            .map((item) => `
                <tr>
                    <td>#${item.id}</td>
                    <td>${item.hazard_type}</td>
                    <td>${item.location}</td>
                    <td><span class="badge ${classifySeverity(item.severity)}">${formatFilterLabel(item.severity)}</span></td>
                    <td>${Math.round(item.confidence * 100)}%</td>
                    <td>${formatDateTime(item.reported_at)}</td>
                    <td><span class="badge ${classifyStatus(item.status)}">${statusLabelMap[item.status]}</span></td>
                    <td><button type="button" class="table-action" data-report-id="${item.id}">Open</button></td>
                </tr>
            `)
            .join("");

        document.querySelectorAll(".table-action").forEach((button) => {
            button.addEventListener("click", () => {
                loadDetail(button.dataset.reportId);
                document.querySelector('[data-section="detail"]').click();
            });
        });
    }

    function updatePagination() {
        const pagination = state.reportPagination;
        document.getElementById("paginationStatus").textContent =
            `Page ${pagination.page} of ${pagination.total_pages} • ${pagination.total} records`;
    }

    function renderBarChart(canvasId, config, horizontal = false) {
        destroyChart(canvasId);
        state.charts[canvasId] = new Chart(document.getElementById(canvasId), {
            type: "bar",
            data: config,
            options: baseChartOptions(horizontal),
        });
    }

    function renderLineChart(canvasId, labels, data) {
        destroyChart(canvasId);
        state.charts[canvasId] = new Chart(document.getElementById(canvasId), {
            type: "line",
            data: {
                labels,
                datasets: [
                    {
                        label: "Detections",
                        data,
                        borderColor: "#f97316",
                        backgroundColor: "rgba(249, 115, 22, 0.16)",
                        tension: 0.35,
                        fill: true,
                    },
                ],
            },
            options: baseChartOptions(false),
        });
    }

    function renderDoughnutChart(canvasId, items) {
        destroyChart(canvasId);
        state.charts[canvasId] = new Chart(document.getElementById(canvasId), {
            type: "doughnut",
            data: {
                labels: items.map((item) => formatFilterLabel(item.label)),
                datasets: [
                    {
                        data: items.map((item) => item.count),
                        backgroundColor: items.map((item) => severityColors[item.label] || "#64748b"),
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom" },
                },
            },
        });
    }

    function baseChartOptions(horizontal) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: horizontal ? "y" : "x",
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(148, 163, 184, 0.15)" },
                },
                x: {
                    grid: { color: "rgba(148, 163, 184, 0.08)" },
                },
            },
            plugins: {
                legend: { position: "bottom" },
            },
        };
    }

    function destroyChart(canvasId) {
        if (state.charts[canvasId]) {
            state.charts[canvasId].destroy();
        }
    }

    function syncReportFilters() {
        state.reportFilters = {
            search: document.getElementById("reportSearch").value.trim(),
            hazard_type: document.getElementById("reportHazardFilter").value,
            severity: document.getElementById("reportSeverityFilter").value,
            status: document.getElementById("reportStatusFilter").value,
            start_date: document.getElementById("reportStartDate").value,
            end_date: document.getElementById("reportEndDate").value,
        };
    }

    function syncMapFilters() {
        state.mapFilters = {
            hazard_type: document.getElementById("mapHazardFilter").value,
            severity: document.getElementById("mapSeverityFilter").value,
            status: document.getElementById("mapStatusFilter").value,
            start_date: document.getElementById("mapStartDate").value,
            end_date: document.getElementById("mapEndDate").value,
        };
    }

    function classifySeverity(severity) {
        return `severity-${severity}`;
    }

    function classifyStatus(status) {
        return `status-${status.replace(/\s+/g, "-")}`;
    }

    function formatDateTime(value) {
        const date = new Date(value);
        return new Intl.DateTimeFormat("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        }).format(date);
    }

    async function fetchJson(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Request failed for ${url}`);
        }
        return response.json();
    }
})();
