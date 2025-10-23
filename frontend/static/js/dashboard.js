function dashboard() {
  return {
    filters: {
      project: '',
      criticity: '',
      status: '',
      search: '',
    },
    applications: [],
    metrics: null,
    projectsById: {},
    projectOptions: [],
    token: null,
    credentials: { email: '', password: '' },
    remediationChart: null,
    timelineChart: null,
    async init() {
      this.token = window.localStorage.getItem('obs_token');
      if (this.token) {
        await this.loadProjects();
        await this.loadMetrics();
        await this.loadApplications();
      }
    },
    async login() {
      try {
        const response = await fetch(`${this.apiBase()}/auth/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.credentials),
        });
        if (!response.ok) throw new Error('Identifiants invalides');
        const data = await response.json();
        this.token = data.access_token;
        window.localStorage.setItem('obs_token', this.token);
        await this.loadProjects();
        await this.loadMetrics();
        await this.loadApplications();
      } catch (error) {
        console.error(error);
        alert("Échec de l'authentification");
      }
    },
    logout() {
      this.token = null;
      window.localStorage.removeItem('obs_token');
      this.applications = [];
      this.metrics = null;
      if (this.remediationChart) {
        this.remediationChart.destroy();
        this.remediationChart = null;
      }
      if (this.timelineChart) {
        this.timelineChart.destroy();
        this.timelineChart = null;
      }
    },
    apiBase() {
      return '/api/v1';
    },
    resetFilters() {
      this.filters = { project: '', criticity: '', status: '', search: '' };
      this.loadApplications();
    },
    async authorizedFetch(url, options = {}) {
      const opts = { ...options, headers: { ...(options.headers || {}) } };
      if (this.token) {
        opts.headers.Authorization = `Bearer ${this.token}`;
      }
      const response = await fetch(url, opts);
      if (response.status === 401) {
        this.logout();
        throw new Error('Non authentifié');
      }
      return response;
    },
    async loadProjects() {
      try {
        const response = await this.authorizedFetch(`${this.apiBase()}/projects/`);
        if (!response.ok) throw new Error('Erreur chargement projets');
        const projects = await response.json();
        this.projectOptions = projects;
        this.projectsById = Object.fromEntries(projects.map((p) => [p.id, p.name]));
      } catch (error) {
        console.error(error);
      }
    },
    async loadApplications() {
      const params = new URLSearchParams();
      if (this.filters.project) params.append('project_id', this.filters.project);
      if (this.filters.criticity) params.append('criticity', this.filters.criticity);
      if (this.filters.status) params.append('status', this.filters.status);
      if (this.filters.search) params.append('search', this.filters.search);
      try {
        const response = await this.authorizedFetch(`${this.apiBase()}/applications/?${params.toString()}`);
        if (!response.ok) throw new Error('Erreur chargement applications');
        this.applications = await response.json();
      } catch (error) {
        console.error(error);
      }
    },
    async loadMetrics() {
      try {
        const response = await this.authorizedFetch(`${this.apiBase()}/dashboard/metrics`);
        if (!response.ok) throw new Error('Erreur chargement métriques');
        this.metrics = await response.json();
        this.renderCharts();
      } catch (error) {
        console.error(error);
      }
    },
    renderCharts() {
      if (!this.metrics) return;
      const remediationCtx = document.getElementById('remediationChart');
      const timelineCtx = document.getElementById('timelineChart');
      const remediationData = this.metrics.remediation_stats || [];
      const timelineData = this.metrics.timeline_histogram || {};

      if (remediationCtx) {
        if (this.remediationChart) this.remediationChart.destroy();
        this.remediationChart = new Chart(remediationCtx, {
          type: 'doughnut',
          data: {
            labels: remediationData.map((item) => item.status),
            datasets: [
              {
                data: remediationData.map((item) => item.count),
                backgroundColor: ['#4f46e5', '#10b981', '#f59e0b', '#ef4444'],
              },
            ],
          },
          options: {
            responsive: true,
            plugins: {
              legend: { position: 'bottom' },
            },
          },
        });
      }

      if (timelineCtx) {
        if (this.timelineChart) this.timelineChart.destroy();
        const labels = Object.keys(timelineData).sort();
        this.timelineChart = new Chart(timelineCtx, {
          type: 'bar',
          data: {
            labels,
            datasets: [
              {
                label: 'Échéances',
                data: labels.map((label) => timelineData[label]),
                backgroundColor: '#6366f1',
              },
            ],
          },
          options: {
            responsive: true,
            scales: {
              y: { beginAtZero: true },
            },
          },
        });
      }
    },
    badgeColor(color) {
      return {
        red: 'bg-red-100 text-red-800',
        orange: 'bg-orange-100 text-orange-800',
        green: 'bg-green-100 text-green-800',
        grey: 'bg-gray-100 text-gray-800',
      }[color] || 'bg-gray-100 text-gray-800';
    },
    exportCsv() {
      const params = new URLSearchParams();
      if (this.filters.project) params.append('project_id', this.filters.project);
      if (this.filters.criticity) params.append('criticity', this.filters.criticity);
      if (this.filters.status) params.append('status', this.filters.status);
      if (this.filters.search) params.append('search', this.filters.search);
      this.authorizedFetch(`${this.apiBase()}/inventory/export?${params.toString()}`)
        .then((response) => response.blob())
        .then((blob) => {
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = 'inventory_export.csv';
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.URL.revokeObjectURL(url);
        })
        .catch((error) => console.error('Export échoué', error));
    },
  };
}
