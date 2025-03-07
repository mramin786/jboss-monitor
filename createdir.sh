# Create the main frontend project directory
mkdir -p jboss-monitor-frontend

# Create subdirectories
mkdir -p jboss-monitor-frontend/public
mkdir -p jboss-monitor-frontend/src
mkdir -p jboss-monitor-frontend/src/api
mkdir -p jboss-monitor-frontend/src/components
mkdir -p jboss-monitor-frontend/src/components/common
mkdir -p jboss-monitor-frontend/src/components/auth
mkdir -p jboss-monitor-frontend/src/components/hosts
mkdir -p jboss-monitor-frontend/src/components/monitor
mkdir -p jboss-monitor-frontend/src/components/reports
mkdir -p jboss-monitor-frontend/src/contexts
mkdir -p jboss-monitor-frontend/src/pages
mkdir -p jboss-monitor-frontend/src/utils
mkdir -p jboss-monitor-frontend/src/themes

# Create empty files
touch jboss-monitor-frontend/public/index.html
touch jboss-monitor-frontend/public/favicon.ico
touch jboss-monitor-frontend/public/manifest.json

touch jboss-monitor-frontend/src/index.js
touch jboss-monitor-frontend/src/App.js
touch jboss-monitor-frontend/src/App.css

touch jboss-monitor-frontend/src/api/auth.js
touch jboss-monitor-frontend/src/api/hosts.js
touch jboss-monitor-frontend/src/api/monitor.js
touch jboss-monitor-frontend/src/api/reports.js

touch jboss-monitor-frontend/src/components/common/Header.js
touch jboss-monitor-frontend/src/components/common/Sidebar.js
touch jboss-monitor-frontend/src/components/common/Footer.js
touch jboss-monitor-frontend/src/components/common/StatusBadge.js
touch jboss-monitor-frontend/src/components/common/LoadingSpinner.js

touch jboss-monitor-frontend/src/components/auth/LoginForm.js
touch jboss-monitor-frontend/src/components/auth/RegisterForm.js

touch jboss-monitor-frontend/src/components/hosts/HostsTable.js
touch jboss-monitor-frontend/src/components/hosts/AddHostForm.js
touch jboss-monitor-frontend/src/components/hosts/BulkImportForm.js
touch jboss-monitor-frontend/src/components/hosts/HostDetails.js

touch jboss-monitor-frontend/src/components/monitor/DashboardOverview.js
touch jboss-monitor-frontend/src/components/monitor/StatusCard.js
touch jboss-monitor-frontend/src/components/monitor/DatasourceStatus.js
touch jboss-monitor-frontend/src/components/monitor/DeploymentStatus.js

touch jboss-monitor-frontend/src/components/reports/ReportsList.js
touch jboss-monitor-frontend/src/components/reports/GenerateReportForm.js
touch jboss-monitor-frontend/src/components/reports/ReportDetails.js

touch jboss-monitor-frontend/src/contexts/AuthContext.js
touch jboss-monitor-frontend/src/contexts/ThemeContext.js

touch jboss-monitor-frontend/src/pages/LoginPage.js
touch jboss-monitor-frontend/src/pages/RegisterPage.js
touch jboss-monitor-frontend/src/pages/DashboardPage.js
touch jboss-monitor-frontend/src/pages/HostsPage.js
touch jboss-monitor-frontend/src/pages/MonitorPage.js
touch jboss-monitor-frontend/src/pages/ReportsPage.js

touch jboss-monitor-frontend/src/utils/auth.js
touch jboss-monitor-frontend/src/utils/api.js
touch jboss-monitor-frontend/src/utils/formatters.js

touch jboss-monitor-frontend/src/themes/darkTheme.js

touch jboss-monitor-frontend/package.json
touch jboss-monitor-frontend/README.md

echo "Frontend project structure created successfully!"

