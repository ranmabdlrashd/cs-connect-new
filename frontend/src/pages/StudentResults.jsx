import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Award, 
  Download,
  AlertCircle,
  RefreshCw,
  Inbox,
  ArrowRight,
  TrendingUp,
  ChevronDown
} from 'lucide-react';
import Sidebar from '../components/Sidebar';
import Topbar from '../components/Topbar';
import '../styles/dashboard.css';
import '../styles/results.css';

const StudentResults = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [selectedSem, setSelectedSem] = useState(6);

  const checkAuthAndFetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('cs_connect_token');
      if (!token) {
        setUser({
          id: 1,
          name: 'Sarah Connor',
          roll_no: 'CS25001',
          branch: 'CSE',
          batch: '2025',
          semester: '6'
        });
      }

      // Mock API delay
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Mock API Response
      setData({
        overall_cgpa: 8.92,
        cgpa_improvement: 0.15,
        prev_sem: 5,
        earned_credits: 105,
        total_credits: 160,
        rank_percentile: 12,
        semester_results: [
          { semester: 1, sgpa: 8.5, credits: 20 },
          { semester: 2, sgpa: 8.7, credits: 20 },
          { semester: 3, sgpa: 9.1, credits: 24 },
          { semester: 4, sgpa: 8.8, credits: 24 },
          { semester: 5, sgpa: 9.2, credits: 22 },
          { semester: 6, sgpa: 0, credits: 20, isCurrent: true }
        ],
        current_semester_marks: [
          { subject_name: "Database Management Systems", subject_code: "CS302", internal: 45, external: 0, total_marks: 45, grade: "A+", grade_points: 10, credits: 4 },
          { subject_name: "Computer Networks", subject_code: "CS304", internal: 42, external: 0, total_marks: 42, grade: "A", grade_points: 9, credits: 4 },
          { subject_name: "Operating Systems", subject_code: "CS306", internal: 38, external: 0, total_marks: 38, grade: "B+", grade_points: 8, credits: 3 },
          { subject_name: "Theory of Computation", subject_code: "CS308", internal: 35, external: 0, total_marks: 35, grade: "B", grade_points: 7, credits: 4 },
          { subject_name: "Software Engineering", subject_code: "CS310", internal: 46, external: 0, total_marks: 46, grade: "A+", grade_points: 10, credits: 3 },
          { subject_name: "Mini Project", subject_code: "CS332", internal: 48, external: 0, total_marks: 48, grade: "A+", grade_points: 10, credits: 2 }
        ],
        grade_distribution: { 'A+': 12, 'A': 15, 'B+': 8, 'B': 4, 'C': 1 }
      });
      
    } catch (err) {
      setError('Failed to load results data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuthAndFetchData();
  }, []);

  const getGradePillClass = (grade) => {
    if (grade.startsWith('A')) return 'status-safe';
    if (grade.startsWith('B')) return 'status-warn';
    if (grade.startsWith('C')) return 'status-danger';
    return 'status-neutral';
  };

  const getGradeCircleClass = (grade) => {
    if (grade === 'A+') return 'grade-A-plus';
    if (grade === 'A') return 'grade-A';
    if (grade === 'B+') return 'grade-B-plus';
    if (grade === 'B') return 'grade-B';
    if (grade === 'C') return 'grade-C';
    return '';
  };

  const renderSkeletonGrids = () => (
    <div className="bento-grid">
      <div className="bento-card col-span-1 skeleton" style={{ height: '280px' }}></div>
      <div className="bento-card col-span-3 skeleton" style={{ height: '280px' }}></div>
      <div className="bento-card col-span-4 skeleton" style={{ height: '400px' }}></div>
      <div className="bento-card col-span-2 skeleton" style={{ height: '300px' }}></div>
      <div className="bento-card col-span-2 skeleton" style={{ height: '300px' }}></div>
    </div>
  );

  return (
    <div className="dashboard-layout">
      <Sidebar user={user} activePath="/dashboard/results" />
      
      <div className="dashboard-main">
        <Topbar 
          breadcrumb="CS Connect · Results & CGPA" 
        />
        
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

          <div className="dashboard-header result-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 className="welcome-title">Results & CGPA</h1>
              <div className="welcome-subtitle">
                B.Tech {user?.branch || 'CSE'} · KTU 2019 Scheme · All Semesters
              </div>
            </div>
            
            <div className="results-header-actions">
              <div className="download-link">
                Download Transcript <ArrowRight size={14} strokeWidth={2} />
              </div>
            </div>
          </div>

          {loading || !data ? (
            renderSkeletonGrids()
          ) : (
            <div className="bento-grid">
              
              {/* === TOP SECTION === */}
              
              {/* Left - CGPA Feature Card */}
              <div className="bento-card col-span-1">
                <div className="cgpa-label">Cumulative GPA</div>
                <div className="cgpa-value">{data.overall_cgpa} <span style={{ fontSize: '24px', color: 'var(--text-dim)' }}>/ 10</span></div>
                <div className="cgpa-trend">
                  <TrendingUp size={12} strokeWidth={2} style={{ display: 'inline', marginRight: '4px' }} />
                  {data.cgpa_improvement} from Semester {data.prev_sem}
                </div>
                <div className="cgpa-rank">
                  Top {data.rank_percentile}% of batch · {user?.batch || '2025'}
                </div>
                
                <div className="credits-divider">
                  <div className="credits-info">
                    <span>Credits Earned</span>
                    <span>{data.earned_credits} / {data.total_credits}</span>
                  </div>
                  <div className="progress-container" style={{ marginTop: 0 }}>
                    <div className="progress-track" style={{ height: '6px' }}>
                      <div 
                        className="progress-fill" 
                        style={{ 
                          width: `${(data.earned_credits / data.total_credits) * 100}%`,
                          backgroundColor: 'var(--green)'
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right - Semester SGPA Grid */}
              <div className="col-span-3">
                <div className="sgpa-grid">
                  {data.semester_results.map((sem, idx) => (
                    <div key={idx} className={`sgpa-card ${sem.isCurrent ? 'current' : ''}`}>
                      {sem.isCurrent && <div className="current-badge">Current</div>}
                      <div className="sem-label">Semester {sem.semester}</div>
                      <div className="sem-sgpa">{sem.sgpa > 0 ? sem.sgpa.toFixed(2) : '--'}</div>
                      <div className="sem-credits">Credits: {sem.credits}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* === DETAILED MARKS TABLE === */}
              <div className="bento-card col-span-4" style={{ padding: '0' }}>
                <div style={{ padding: '24px 24px 0 24px' }}>
                  <div className="panel-header-row">
                    <h3 className="card-title" style={{ margin: 0 }}>Semester {selectedSem} &mdash; Detailed Marks</h3>
                    <div className="view-all-link">View All Semesters <ArrowRight size={12} style={{ display: 'inline' }} /></div>
                  </div>
                </div>
                
                <div className="marks-table-container">
                  <table className="marks-table">
                    <thead>
                      <tr>
                        <th>Subject</th>
                        <th>Code</th>
                        <th>Internal (/50)</th>
                        <th>External (/100)</th>
                        <th>Total (/150)</th>
                        <th>Grade</th>
                        <th>Points</th>
                        <th>Credits</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.current_semester_marks.map((mark, idx) => (
                        <tr key={idx}>
                          <td className="subject-col">{mark.subject_name}</td>
                          <td className="code-col">{mark.subject_code}</td>
                          <td style={{ color: 'var(--text-muted)' }}>{mark.internal}</td>
                          <td>
                            <div className="inline-bar-container">
                              <span>{mark.external > 0 ? mark.external : '--'}</span>
                              <div className="inline-bar">
                                <div className="inline-bar-fill" style={{ width: `${mark.external}%`, backgroundColor: mark.external > 0 ? 'var(--cream)' : 'transparent' }}></div>
                              </div>
                            </div>
                          </td>
                          <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{mark.total_marks}</td>
                          <td>
                            <span className={`status-pill ${getGradePillClass(mark.grade)}`}>
                              {mark.grade}
                            </span>
                          </td>
                          <td style={{ color: 'var(--cream)' }}>{mark.grade_points}</td>
                          <td style={{ color: 'var(--text-dim)' }}>{mark.credits}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="marks-footer-row">
                        <td colSpan="5"></td>
                        <td colSpan="3" style={{ textAlign: 'right' }}>
                          <span style={{ marginRight: '16px' }}>Semester {selectedSem} SGPA:</span>
                          <span className="sgpa-calc-display">Pending Finals</span>
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {/* === BOTTOM ROW === */}
              
              {/* Left - Current Semester Internal Grades */}
              <div className="bento-card col-span-2">
                <h3 className="card-title" style={{ marginBottom: '4px' }}>Internal Assessments</h3>
                <div className="internal-sub-label">Internals only &middot; Finals pending</div>
                
                <div className="internal-list">
                  {data.current_semester_marks.map((item, idx) => (
                    <div key={idx} className="internal-item">
                      <div className={`grade-circle ${getGradeCircleClass(item.grade)}`}>{item.grade}</div>
                      <div className="internal-details">
                        <div className="internal-subject">{item.subject_name}</div>
                        <div className="internal-meta">{item.internal} / 50 marks &middot; {item.credits} Credits</div>
                      </div>
                      <div className="internal-points">{item.grade_points} pt</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Right - Grade Distribution Chart */}
              <div className="bento-card col-span-2">
                <h3 className="card-title">Grade Distribution (Overall)</h3>
                
                <div className="dist-chart-container">
                  {['A+', 'A', 'B+', 'B', 'C'].map((grade) => {
                    const count = data.grade_distribution[grade] || 0;
                    const maxCount = Math.max(...Object.values(data.grade_distribution));
                    const widthPercent = maxCount > 0 ? (count / maxCount) * 100 : 0;
                    
                    return (
                      <div key={grade} className="dist-bar-row">
                        <div className="dist-label">{grade}</div>
                        <div className="dist-bar-track">
                          <div 
                            className="dist-bar-fill" 
                            style={{ width: `${widthPercent}%` }}
                          ></div>
                        </div>
                        <div className="dist-count">{count}</div>
                      </div>
                    );
                  })}
                  
                  <div className="dist-summary">
                    <span>Total Subjects: {Object.values(data.grade_distribution).reduce((a, b) => a + b, 0)}</span>
                    <span>0 Active Backlogs</span>
                  </div>
                </div>
              </div>

            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentResults;
