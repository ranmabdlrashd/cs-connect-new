import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import StudentDashboard from './pages/StudentDashboard';
import StudentAttendance from './pages/StudentAttendance';
import StudentResults from './pages/StudentResults';
import ComingSoon from './pages/ComingSoon';
import './styles/dashboard.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<StudentDashboard />} />
        <Route path="/dashboard/academics" element={<ComingSoon />} />
        <Route path="/dashboard/attendance" element={<StudentAttendance />} />
        <Route path="/dashboard/results" element={<StudentResults />} />
        <Route path="/dashboard/assignments" element={<ComingSoon />} />
        <Route path="/dashboard/library" element={<ComingSoon />} />
        <Route path="/dashboard/labs" element={<ComingSoon />} />
        <Route path="/dashboard/faculty" element={<ComingSoon />} />
        <Route path="/dashboard/timetable" element={<ComingSoon />} />
        <Route path="/dashboard/placements" element={<ComingSoon />} />
        <Route path="/settings" element={<ComingSoon />} />
        <Route path="*" element={<div style={{ padding: '2rem', textAlign: 'center' }}><h1>404</h1><p>Page Not Found</p></div>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
