import React from 'react';
import { 
  LayoutDashboard, 
  BookOpen, 
  ClipboardCheck, 
  Award, 
  FileText, 
  BookMarked, 
  FlaskConical, 
  Users, 
  Calendar, 
  Briefcase,
  Settings,
  Layers
} from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

const navItems = [
  { icon: LayoutDashboard, path: '/dashboard', label: 'Dashboard' },
  { icon: BookOpen, path: '/dashboard/academics', label: 'Academics' },
  { icon: ClipboardCheck, path: '/dashboard/attendance', label: 'Attendance' },
  { icon: Award, path: '/dashboard/results', label: 'Results & CGPA' },
  { icon: FileText, path: '/dashboard/assignments', label: 'Assignments' },
  { icon: BookMarked, path: '/dashboard/library', label: 'Library' },
  { icon: FlaskConical, path: '/dashboard/labs', label: 'Lab Bookings' },
  { icon: Users, path: '/dashboard/faculty', label: 'Faculty' },
  { icon: Calendar, path: '/dashboard/timetable', label: 'Timetable' },
  { icon: Briefcase, path: '/dashboard/placements', label: 'Placements' }
];

const Sidebar = ({ user }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const getInitials = (name) => {
    if (!name) return 'ST';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <Layers size={20} />
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.path === '/dashboard' ? location.pathname === '/dashboard' : location.pathname.startsWith(item.path);
          return (
            <div 
              key={item.path}
              className={`nav-item ${isActive ? 'active' : ''}`}
              title={item.label}
              onClick={() => {
                const flaskRoutes = ['/dashboard/assignments', '/dashboard/library', '/dashboard/labs', '/dashboard/faculty', '/dashboard/timetable', '/dashboard/placements', '/timetable', '/placements'];
                if (flaskRoutes.includes(item.path)) {
                  window.location.href = item.path;
                } else {
                  navigate(item.path);
                }
              }}
            >
              <Icon size={20} strokeWidth={1.5} />
            </div>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <div className="nav-item" title="Settings" onClick={() => navigate('/settings')}>
          <Settings size={20} strokeWidth={1.5} />
        </div>
        <div className="sidebar-avatar" title={user?.name}>
          {getInitials(user?.name)}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
