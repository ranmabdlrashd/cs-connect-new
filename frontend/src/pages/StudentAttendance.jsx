import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  AlertCircle,
  RefreshCw,
  Download,
  Mail,
  CheckCircle,
  AlertTriangle,
  XCircle,
  TrendingUp,
  Info
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Topbar from '../components/Topbar';

const StudentAttendance = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    overall_percentage: 0,
    classes_attended: 0,
    classes_held: 0,
    subjects: [],
    monthly_trend: []
  });

  const checkAuthAndFetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/student/attendance');
      if (!response.ok) throw new Error('Unauthorized');
      const attendanceData = await response.json();

      const profileRes = await fetch('/api/student/profile');
      const profile = await profileRes.json();
      setUser(profile);
      
      setData({
        ...attendanceData,
        classes_attended: attendanceData.subjects.reduce((a, b) => a + (b.classes_attended || 0), 0),
        classes_held: attendanceData.subjects.reduce((a, b) => a + (b.classes_held || 0), 0)
      });
      
    } catch (err) {
      setError('Failed to load attendance data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuthAndFetchData();
  }, []);

  const getAttendanceColor = (percentage) => {
    if (percentage >= 80) return 'var(--green)';
    if (percentage >= 65) return 'var(--amber)';
    return 'var(--red)';
  };

  const getStatusPill = (percentage) => {
    if (percentage >= 75) return { label: 'Safe', className: 'status-safe', icon: <CheckCircle size={12} style={{marginRight: '4px'}} /> };
    if (percentage >= 65) return { label: 'At Risk', className: 'status-warn', icon: <AlertTriangle size={12} style={{marginRight: '4px'}} /> };
    return { label: 'Low', className: 'status-danger', icon: <XCircle size={12} style={{marginRight: '4px'}} /> };
  };

  const calculateSafeLeaves = (held, attended) => {
    return Math.floor((held * 0.25) - (held - attended));
  };

  const renderSkeleton = () => (
    <div className="bento-grid">
      <div className="bento-card col-span-1 skeleton" style={{ height: '140px' }}></div>
      <div className="bento-card col-span-1 skeleton" style={{ height: '140px' }}></div>
      <div className="bento-card col-span-1 skeleton" style={{ height: '140px' }}></div>
      <div className="bento-card col-span-1 skeleton" style={{ height: '140px' }}></div>
      <div className="bento-card col-span-4 skeleton" style={{ height: '400px' }}></div>
      <div className="bento-card col-span-2 skeleton" style={{ height: '240px' }}></div>
      <div className="bento-card col-span-2 skeleton" style={{ height: '240px' }}></div>
    </div>
  );

  const classesMissed = data.classes_held - data.classes_attended;
  const overallSafeLeaves = Math.floor((data.classes_held * 0.25) - classesMissed);
  const overallColor = getAttendanceColor(data.overall_percentage);
  
  const hasLowAttendance = data.subjects.some(sub => sub.percentage < 75);

  return (
    <div className="dashboard-layout">
      {/* Adding styles specifically for tables and specific components missing from dashboard.css */}
      <style>{`
        .table-container { width: 100%; overflow-x: auto; margin-top: 16px; }
        .data-table { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; }
        .data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); }
        .data-table th { font-size: 11px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
        .data-table td { font-size: 13px; color: var(--text-primary); }
        .data-table tbody tr:hover { background-color: var(--bg-hover); }
        
        .inline-prog-container { display: flex; align-items: center; gap: 12px; }
        .inline-prog-track { width: 100px; height: 5px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
        .inline-prog-fill { height: 100%; border-radius: 3px; transition: width 0.3s ease; }
        
        .contact-btn { background: transparent; border: 1px solid var(--border-accent); color: var(--text-primary); padding: 4px 10px; border-radius: 6px; font-size: 11px; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s; }
        .contact-btn:hover { background: rgba(139,29,29,0.1); border-color: rgba(139,29,29,0.4); }
        
        .warning-box { margin-top: 24px; padding: 16px 20px; background-color: rgba(139,29,29,0.08); border: 1px solid rgba(139,29,29,0.2); border-radius: 8px; }
        .warning-title { display: flex; align-items: center; gap: 8px; color: var(--accent); font-size: 14px; font-weight: 600; margin-bottom: 12px; }
        .warning-list { padding-left: 24px; color: var(--text-muted); font-size: 12px; line-height: 1.6; }
        
        .trend-bar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .trend-month { width: 30px; font-size: 11px; color: var(--text-dim); text-transform: uppercase; }
        .trend-track { flex: 1; height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
        
        .rule-box { padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; border: 1px solid transparent; }
        .rule-green { background: rgba(60,180,100,0.08); border-color: rgba(60,180,100,0.2); }
        .rule-amber { background: rgba(180,130,40,0.08); border-color: rgba(180,130,40,0.2); }
        .rule-red { background: rgba(139,29,29,0.08); border-color: rgba(139,29,29,0.2); }
        .rule-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
        .rule-desc { font-size: 11px; color: var(--text-ghost); line-height: 1.4; }
      `}</style>

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
              <h1 className="welcome-title" style={{ fontFamily: "'Playfair Display', serif", fontSize: '22px', color: '#F5E6BE', fontWeight: 700 }}>Attendance Overview</h1>
              <div className="welcome-subtitle">
                Semester {user?.semester || 'N/A'} · 2025-2026 · Batch: {user?.batch || 'N/A'}
              </div>
            </div>
            {user?.semester && (
              <div className="semester-badge">SEMESTER {user.semester}</div>
            )}
          </div>

          {loading ? (
            renderSkeleton()
          ) : (
            <div className="bento-grid">
              
              {/* Summary Cards Row */}
              <div className="bento-card col-span-1 stat-card" style={{ borderBottomColor: overallColor, borderBottomWidth: '2px', borderBottomStyle: 'solid' }}>
                <div>
                  <div className="stat-label">Overall Attendance</div>
                  <div className="stat-value">{data.overall_percentage}%</div>
                  <div className="stat-sub">Average of all subjects</div>
                </div>
              </div>

              <div className="bento-card col-span-1 stat-card" style={{ borderBottomColor: getAttendanceColor((data.classes_attended/data.classes_held)*100), borderBottomWidth: '2px', borderBottomStyle: 'solid' }}>
                <div>
                  <div className="stat-label">Classes Attended</div>
                  <div className="stat-value">{data.classes_attended} <span style={{fontSize: '14px', color: 'var(--text-dim)', fontWeight: 400}}>/ {data.classes_held}</span></div>
                  <div className="stat-sub">Total sessions present</div>
                </div>
              </div>

              <div className="bento-card col-span-1 stat-card" style={{ borderBottomColor: classesMissed > 0 ? 'var(--amber)' : 'var(--text-ghost)', borderBottomWidth: '2px', borderBottomStyle: 'solid' }}>
                <div>
                  <div className="stat-label">Classes Missed</div>
                  <div className="stat-value">{classesMissed}</div>
                  <div className="stat-sub">Total absent sessions</div>
                </div>
              </div>

              <div className="bento-card col-span-1 stat-card" style={{ borderBottomColor: overallSafeLeaves <= 0 ? 'var(--red)' : 'var(--green)', borderBottomWidth: '2px', borderBottomStyle: 'solid' }}>
                <div>
                  <div className="stat-label">Safe Leaves Left</div>
                  <div className="stat-value" style={{ color: overallSafeLeaves <= 0 ? 'var(--red)' : 'var(--cream)' }}>
                    {overallSafeLeaves <= 0 ? 0 : overallSafeLeaves}
                  </div>
                  <div className="stat-sub">Before dipping below 75%</div>
                </div>
              </div>

              {/* Subject-wise Table */}
              <div className="bento-card col-span-4">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 className="card-title" style={{ marginBottom: 0 }}>Subject-wise Attendance</h3>
                  <a href="#" style={{ fontSize: '12px', color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: '4px', textDecoration: 'none' }}>
                    <Download size={14} /> Download Report 
                  </a>
                </div>

                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Subject</th>
                        <th>Faculty</th>
                        <th style={{textAlign: 'center'}}>Held</th>
                        <th style={{textAlign: 'center'}}>Attended</th>
                        <th>Attendance %</th>
                        <th style={{textAlign: 'center'}}>Safe Leaves</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.subjects.map((sub, idx) => {
                        const safeLeaves = calculateSafeLeaves(sub.classes_held, sub.classes_attended);
                        const pColor = getAttendanceColor(sub.percentage);
                        const status = getStatusPill(sub.percentage);
                        
                        return (
                          <tr key={idx}>
                            <td style={{ fontWeight: 500 }}>{sub.subject_name}</td>
                            <td style={{ color: 'var(--text-muted)' }}>{sub.faculty_name}</td>
                            <td style={{ textAlign: 'center' }}>{sub.classes_held}</td>
                            <td style={{ textAlign: 'center' }}>{sub.classes_attended}</td>
                            <td>
                              <div className="inline-prog-container">
                                <div className="inline-prog-track">
                                  <div className="inline-prog-fill" style={{ width: `${sub.percentage}%`, background: pColor }}></div>
                                </div>
                                <span style={{ color: pColor, fontWeight: 600, fontSize: '13px' }}>{sub.percentage.toFixed(2)}%</span>
                              </div>
                            </td>
                            <td style={{ textAlign: 'center', fontWeight: 600, color: safeLeaves <= 0 ? 'var(--red)' : 'var(--text-primary)' }}>
                              {safeLeaves <= 0 ? '0' : safeLeaves}
                            </td>
                            <td>
                              <span className={`status-pill ${status.className}`} style={{ display: 'flex', alignItems: 'center' }}>
                                {status.icon} {status.label}
                              </span>
                            </td>
                            <td>
                              {sub.percentage < 75 ? (
                                <button className="contact-btn">
                                  <Mail size={12} strokeWidth={2} /> Contact Faculty
                                </button>
                              ) : (
                                <span style={{ color: 'var(--text-ghost)', fontSize: '11px' }}>-</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {hasLowAttendance && (
                  <div className="warning-box">
                    <div className="warning-title">
                      <AlertTriangle size={16} strokeWidth={2} />
                      Attention Required: Low Attendance
                    </div>
                    <ul className="warning-list">
                      {data.subjects.filter(s => s.percentage < 75).map((sub, i) => (
                        <li key={i}>
                          <strong>{sub.subject_name}</strong>: Currently at {sub.percentage}%. You need to attend the next {Math.ceil(((0.75 * sub.classes_held) - sub.classes_attended) / 0.25)} consecutive classes to reach the safe zone. Please contact {sub.faculty_name}.
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Bottom Row */}
              {/* Monthly Trend */}
              <div className="bento-card col-span-2">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
                  <TrendingUp size={18} color="var(--cream)" />
                  <h3 className="card-title" style={{ marginBottom: 0 }}>Monthly Trend</h3>
                </div>
                
                <div style={{ paddingRight: '20px' }}>
                  {data.monthly_trend.map((m, i) => {
                    const mColor = getAttendanceColor(m.percentage);
                    return (
                      <div key={i} className="trend-bar-row">
                        <span className="trend-month">{m.month}</span>
                        <div className="trend-track">
                          <div className="inline-prog-fill" style={{ width: `${m.percentage}%`, background: mColor }}></div>
                        </div>
                        <span style={{ fontSize: '11px', color: mColor, fontWeight: 600, width: '40px', textAlign: 'right' }}>{m.percentage}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Attendance Rules */}
              <div className="bento-card col-span-2">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
                  <Info size={18} color="var(--cream)" />
                  <h3 className="card-title" style={{ marginBottom: 0 }}>Attendance Policy</h3>
                </div>

                <div className="rule-box rule-green">
                  <div className="rule-title" style={{ color: 'var(--green)' }}>≥ 75% — Minimum Required</div>
                  <div className="rule-desc">Students maintaining 75% or above are directly eligible for terminal semester examinations.</div>
                </div>

                <div className="rule-box rule-amber">
                  <div className="rule-title" style={{ color: 'var(--amber)' }}>65–74% — Condonation Zone</div>
                  <div className="rule-desc">Requires condonation approval from HOD/Principal and payment of condonation fee.</div>
                </div>

                <div className="rule-box rule-red">
                  <div className="rule-title" style={{ color: 'var(--red)' }}>Below 65% — Not Eligible</div>
                  <div className="rule-desc">Strictly not eligible to appear for the terminal semester university examination.</div>
                </div>
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentAttendance;
