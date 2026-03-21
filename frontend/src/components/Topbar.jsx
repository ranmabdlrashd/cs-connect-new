import React from 'react';
import { Search, Bell } from 'lucide-react';

const Topbar = () => {
  return (
    <div className="topbar">
      <div className="breadcrumb">
        <span className="breadcrumb-item">CS Connect</span> · Dashboard
      </div>
      
      <div className="search-container">
        <div className="search-input-wrapper">
          <Search className="search-icon" strokeWidth={1.5} />
          <input 
            type="text" 
            className="search-input" 
            placeholder="Search..." 
          />
        </div>
        
        <button className="notification-btn">
          <Bell size={18} strokeWidth={1.5} />
          <span className="notification-dot"></span>
        </button>
      </div>
    </div>
  );
};

export default Topbar;
