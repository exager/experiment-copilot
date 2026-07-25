import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  PlusCircle,
  Play,
  FileText,
} from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/create', icon: PlusCircle, label: 'New Experiment' },
  { to: '/running', icon: Play, label: 'Running Experiments' },
  { to: '/reports', icon: FileText, label: 'Reports' },
]

export default function Layout() {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-56 bg-[#1E1B4B] flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b border-indigo-800">
          <h1 className="text-white font-bold text-lg">AI Copilot</h1>
          <p className="text-indigo-300 text-xs">Decision Intelligence</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-purple-600 text-white'
                    : 'text-indigo-200 hover:bg-indigo-800 hover:text-white'
                }`
              }
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-indigo-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white text-xs font-bold">
              PM
            </div>
            <div>
              <p className="text-white text-sm font-medium">Product Manager</p>
              <p className="text-indigo-300 text-xs">Growth Team</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-50 to-slate-100">
        <Outlet />
      </main>
    </div>
  )
}
