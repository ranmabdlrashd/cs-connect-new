import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import StudentDashboard from './pages/StudentDashboard';
import StudentAttendance from './pages/StudentAttendance';
import StudentResults from './pages/StudentResults';
import './styles/dashboard.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<StudentDashboard />} />
        <Route path="/dashboard/attendance" element={<StudentAttendance />} />
        <Route path="/dashboard/results" element={<StudentResults />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
