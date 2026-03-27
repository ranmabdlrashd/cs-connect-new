import React from 'react';
import { useLocation } from 'react-router-dom';
import { Construction } from 'lucide-react';

const ComingSoon = () => {
    const location = useLocation();
    const pageName = location.pathname.split('/').pop().charAt(0).toUpperCase() + location.pathname.split('/').pop().slice(1);

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            padding: '40px',
            textAlign: 'center',
            color: '#8B1111'
        }}>
            <Construction size={48} style={{ marginBottom: '20px', opacity: 0.6 }} />
            <h1 style={{ fontFamily: 'Playfair Display', fontSize: '32px', marginBottom: '10px' }}>
                {pageName} Coming Soon
            </h1>
            <p style={{ fontSize: '16px', opacity: 0.8, maxWidth: '400px' }}>
                We're currently migrating this section to our new React-based architecture. 
                Stay tuned for updates!
            </p>
        </div>
    );
};

export default ComingSoon;
