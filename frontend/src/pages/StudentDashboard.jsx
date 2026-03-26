import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ClipboardCheck, 
  Award, 
  BookOpen, 
  FileText,
  Download,
  CheckCircle,
  FlaskConical,
  Calendar,
  Briefcase,
  AlertCircle,
  RefreshCw,
  Inbox
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Topbar from '../components/Topbar';

const StudentDashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    dashboard: null,
    schedule: null,
    notices: null
  });

  const checkAuthAndFetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/student/dashboard');
      if (!response.ok) throw new Error('Unauthorized or Server Error');
      const dashboardData = await response.json();
      
      setUser(dashboardData.user);

      const [schedRes, noticeRes] = await Promise.all([
        fetch('/api/student/schedule'),
        fetch('/api/notices?limit=5')
      ]);
      
      const schedule = await schedRes.json();
      const notices = await noticeRes.json();

      setData({
        dashboard: dashboardData.dashboard,
        schedule: schedule.classes.map(c => ({
          time: `${c.time_start} - ${c.time_end}`,
          subject: c.subject_name,
          room: 'LHC', // Room info missing in DB, defaulting
          faculty: c.faculty_name,
          status: 'future' 
        })),
        notices: notices
      });
      
    } catch (err) {
      setError('Failed to load dashboard data. Please check your connection.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuthAndFetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getAttendanceColor = (percentage) => {
    if (percentage >= 80) return 'var(--green)';
    if (percentage >= 65) return 'var(--amber)';
    return 'var(--red)';
  };

  const getLibraryStatus = (days) => {
    if (days < 0) return { text: `Overdue by ${Math.abs(days)} days`, color: 'var(--red)' };
    if (days <= 5) return { text: `Due in ${days} days`, color: 'var(--amber)' };
    return { text: `Due in ${days} days`, color: 'var(--text-dim)' };
  };

  const getGradePillClass = (grade) => {
    if (grade.startsWith('A')) return 'status-safe';
    if (grade.startsWith('B')) return 'status-warn';
    return 'status-danger';
  };

  const renderSkeletonGrids = () => (
    <div className="bento-grid">
      <div className="bento-card col-span-1 skeleton" style={{ height: '160px' }}></div>
      <div className="bento-card col-span-1 skeleton" style={{ height: '160px' }}></div>
      <div className="bento-card col-span-1 skeleton" style={{ height: '160px' }}></div>
      <div className="bento-card col-span-1 skeleton" style={{ height: '160px' }}></div>
      
      <div className="bento-card col-span-2 skeleton" style={{ height: '300px' }}></div>
      <div className="bento-card col-span-2 skeleton" style={{ height: '300px' }}></div>
      
      <div className="bento-card col-span-2 skeleton" style={{ height: '240px' }}></div>
      <div className="bento-card col-span-2 skeleton" style={{ height: '240px' }}></div>
    </div>
  );

  return (
    <div className="dashboard-layout">
      <Sidebar user={user} />
      
      <div className="dashboard-main">
        <Topbar />
        
        <div className="dashboard-content">
          {error && (
            <div className="error-banner">
              <div className="error-text">
                <AlertCircle size={16} strokeWidth={1.5} />
                <span>{error}</span>
              </div>
              <button className="retry-btn" onClick={checkAuthAndFetchData}>
                <RefreshCw size={12} strokeWidth={2} style={{ marginRight: '4px', display: 'inline' }} />
                Retry
              </button>
            </div>
          )}

          <div className="dashboard-header">
            <div>
              <h1 className="welcome-title">Welcome back, {user?.name || 'Student'}</h1>
              <div className="welcome-subtitle">
                {user?.batch || '2025'} · {user?.roll_no || 'CS0000'}
              </div>
            </div>
            
            {user?.semester && (
              <div className="semester-badge">
                SEMESTER {user.semester}
              </div>
            )}
          </div>

          {loading ? (
            renderSkeletonGrids()
          ) : (
            <div className="bento-grid">
              
              {/* === ROW 1 === */}
              
              {/* Card 1: Attendance */}
              <div className="bento-card col-span-1 stat-card">
                <div>
                  <div className="stat-label">Attendance</div>
                  <div className="stat-value">{data.dashboard?.attendance?.percentage || 0}%</div>
                  <div className="stat-sub">82% minimum required</div>
                </div>
                
                <div className="progress-container">
                  <div className="progress-track">
                    <div 
                      className="progress-fill" 
                      style={{ 
                        width: `${Math.min(100, data.dashboard?.attendance?.percentage || 0)}%`,
                        backgroundColor: getAttendanceColor(data.dashboard?.attendance?.percentage || 0)
                      }}
                    ></div>
                  </div>
                </div>
                
                <div className="stat-icon">
                  <ClipboardCheck size={28} strokeWidth={1.5} />
                </div>
                
                <div 
                  style={{ 
                    position: 'absolute', bottom: 0, left: 0, right: 0, height: '2px',
                    backgroundColor: getAttendanceColor(data.dashboard?.attendance?.percentage || 0)
                  }}
                ></div>
              </div>

              {/* Card 2: CGPA */}
              <div className="bento-card col-span-1 stat-card">
                <div>
                  <div className="stat-label">Current CGPA</div>
                  <div className="stat-value">{data.dashboard?.cgpa?.current || '0.00'}</div>
                  <div className="stat-sub" style={{ color: data.dashboard?.cgpa?.isPositive ? '#3a8834' : 'var(--text-dim)' }}>
                    {data.dashboard?.cgpa?.isPositive ? '↑' : '↓'} {data.dashboard?.cgpa?.change} from last semester
                  </div>
                </div>
                
                <div className="stat-icon">
                  <Award size={28} strokeWidth={1.5} />
                </div>
              </div>

              {/* Card 3: Library Books */}
              <div className="bento-card col-span-1 stat-card">
                <div>
                  <div className="stat-label">Library Books</div>
                  <div className="stat-value">{data.dashboard?.library?.borrowed_count || 0} / 4</div>
                  
                  {data.dashboard?.library?.borrowed_count > 0 ? (
                    <div className="stat-sub" style={{ color: getLibraryStatus(data.dashboard?.library?.nearest_due_days).color }}>
                      {getLibraryStatus(data.dashboard?.library?.nearest_due_days).text}
                    </div>
                  ) : (
                    <div className="stat-sub">No active loans</div>
                  )}
                </div>
                
                <div className="stat-icon">
                  <BookOpen size={28} strokeWidth={1.5} />
                </div>
              </div>

              {/* Card 4: Assignments */}
              <div className="bento-card col-span-1 stat-card">
                <div>
                  <div className="stat-label">Assignments</div>
                  <div className="stat-value" style={{ color: 'var(--amber)' }}>
                    {data.dashboard?.assignments?.pending_count || 0}
                  </div>
                  <div className="stat-sub">Pending submissions</div>
                </div>
                
                <div className="stat-icon">
                  <FileText size={28} strokeWidth={1.5} />
                </div>
              </div>

              {/* === ROW 2 === */}
              
              {/* Today's Schedule */}
              <div className="bento-card col-span-2">
                <h3 className="card-title">Today's Schedule &mdash; {new Date().toLocaleDateString('en-US', { weekday: 'long' })}</h3>
                
                {!data.schedule || data.schedule.length === 0 ? (
                  <div className="empty-state">
                    <Calendar size={24} strokeWidth={1.5} />
                    <span className="empty-state-text">No classes scheduled for today</span>
                  </div>
                ) : (
                  <div className="schedule-list">
                    {data.schedule.map((cls, idx) => (
                      <div key={idx} className={`schedule-item ${cls.status === 'current' ? 'current' : ''}`}>
                        <div className={`schedule-dot ${cls.status}`}></div>
                        <div className="schedule-time">{cls.time}</div>
                        <div className="schedule-details">
                          <div className="schedule-subject">{cls.subject}</div>
                          <div className="schedule-meta">
                            <span>{cls.room}</span>
                            <span>·</span>
                            <span>{cls.faculty}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* current Semester Grades */}
              <div className="bento-card col-span-2">
                <h3 className="card-title">Current Semester Grades</h3>
                
                {!data.dashboard?.grades || data.dashboard?.grades.length === 0 ? (
                  <div className="empty-state">
                    <Inbox size={24} strokeWidth={1.5} />
                    <span className="empty-state-text">Grades not yet published</span>
                  </div>
                ) : (
                  <div className="grades-list">
                    {data.dashboard.grades.map((item, idx) => (
                      <div key={idx} className="grade-item">
                        <div className="grade-subject">{item.subject_name}</div>
                        <div className={`status-pill ${getGradePillClass(item.grade)}`}>
                          Grade {item.grade}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* === ROW 3 === */}
              
              {/* Action Hub */}
              <div className="bento-card col-span-2">
                <div className="stat-label" style={{ marginBottom: '16px' }}>Action Hub</div>
                
                <div className="action-grid">
                  <div className="action-btn" onClick={() => window.location.href='/dashboard/syllabus'}>
                    <Download size={16} strokeWidth={1.5} />
                    <span className="action-label">Download Syllabus</span>
                  </div>
                  <div className="action-btn" onClick={() => navigate('/dashboard/results')}>
                    <CheckCircle size={16} strokeWidth={1.5} />
                    <span className="action-label">View Results</span>
                  </div>
                  <div className="action-btn" onClick={() => window.location.href='/dashboard/labs'}>
                    <FlaskConical size={16} strokeWidth={1.5} />
                    <span className="action-label">Lab Bookings</span>
                  </div>
                  <div className="action-btn" onClick={() => window.location.href='/dashboard/assignments'}>
                    <FileText size={16} strokeWidth={1.5} />
                    <span className="action-label">Assignment Portal</span>
                  </div>
                  <div className="action-btn" onClick={() => window.location.href='/dashboard/timetable'}>
                    <Calendar size={16} strokeWidth={1.5} />
                    <span className="action-label">Timetable</span>
                  </div>
                  <div className="action-btn" onClick={() => window.location.href='/dashboard/placements'}>
                    <Briefcase size={16} strokeWidth={1.5} />
                    <span className="action-label">Placement Drives</span>
                  </div>
                </div>
              </div>

              {/* Announcements */}
              <div className="bento-card col-span-2">
                <h3 className="card-title">Recent Announcements</h3>
                
                {!data.notices || data.notices.length === 0 ? (
                  <div className="empty-state">
                    <Inbox size={24} strokeWidth={1.5} />
                    <span className="empty-state-text">No recent announcements</span>
                  </div>
                ) : (
                  <div className="announcement-list">
                    {data.notices.map((notice) => (
                      <div key={notice.id} className="announcement-item">
                        <div className="announcement-dot"></div>
                        <div className="announcement-content">
                          <div className="announcement-title">{notice.title}</div>
                          <div className="announcement-body">{notice.body}</div>
                          <div className="announcement-date">{notice.date}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
