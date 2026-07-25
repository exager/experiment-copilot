import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import NewExperimentPage from './pages/NewExperimentPage'
import RunningExperimentsPage from './pages/RunningExperimentsPage'
import LiveDashboardPage from './pages/LiveDashboardPage'
import ReportsListPage from './pages/ReportsListPage'
import ReportPage from './pages/ReportPage'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/create" element={<NewExperimentPage />} />
        <Route path="/running" element={<RunningExperimentsPage />} />
        <Route path="/experiments/:id" element={<LiveDashboardPage />} />
        <Route path="/reports" element={<ReportsListPage />} />
        <Route path="/experiments/:id/report" element={<ReportPage />} />
      </Route>
    </Routes>
  )
}

export default App
