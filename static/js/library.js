document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');

    function fetchBooks(query = '') {
        fetch(`/search_books?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => renderBooks(data))
            .catch(err => console.error("Error fetching books:", err));
    }

    function renderBooks(books) {
        const grid = document.getElementById('booksGrid');
        const noResults = document.getElementById('noResults');

        grid.innerHTML = '';
        if (books.length === 0) {
            noResults.style.display = 'block';
            return;
        }
        noResults.style.display = 'none';

        books.forEach(book => {
            const isAvail = book.availability !== false;
            const statusClass = isAvail ? 'status-available' : 'status-issued';
            const statusText = isAvail ? 'Available' : 'Issued';

            // For card layout
            const card = document.createElement('div');
            card.className = 'book-card reveal active';
            card.style.cursor = 'pointer';
            card.style.background = 'white';
            card.style.borderRadius = '10px';
            card.style.overflow = 'hidden';
            card.style.boxShadow = '0 4px 15px rgba(0,0,0,0.05)';
            card.onclick = () => { window.location.href = `/book/${book.id}`; };

            let holderInfoHtml = '';
            if (!isAvail && book.current_holder) {
                if (window.USER_ROLE === 'admin') {
                    holderInfoHtml = `<p class="book-holder" style="color: #d9534f; font-size: 0.85em; font-weight: bold; margin-top: 5px;">Currently with: ${book.current_holder}</p>`;
                }
            }

            const subject = book.subject || 'General Collection';
            const author = book.author || 'Unknown Author';
            const title = book.title;
            const icon = book.cover_icon || 'fas fa-book';
            const bg = book.cover_gradient || 'linear-gradient(135deg, #667eea, #764ba2)';

            card.innerHTML = `
                <div class="book-cover" style="height: 140px; background: ${bg}; display: flex; align-items: center; justify-content: center; font-size: 3rem; color: white;">
                    <i class="${icon}"></i>
                </div>
                <div class="book-info" style="padding: 20px;">
                    <h3 class="book-title" style="margin: 0 0 5px 0; font-size: 1.2rem; color: #333;">${title}</h3>
                    <p class="book-author" style="margin: 0 0 15px 0; color: #777; font-size: 0.9rem;">by ${author}</p>
                    
                    <div style="margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.8rem; background: #eee; padding: 3px 8px; border-radius: 4px; color: #555;">${subject}</span>
                        <span style="font-size: 0.8rem; font-weight: bold; padding: 3px 8px; border-radius: 4px; ${isAvail ? 'color: #28a745; background: #d4edda;' : 'color: #dc3545; background: #f8d7da;'}">${statusText}</span>
                    </div>
                    ${holderInfoHtml}
                </div>
            `;
            grid.appendChild(card);
        });
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', () => fetchBooks(searchInput.value));
    }

    if (searchInput) {
        searchInput.addEventListener('keyup', (e) => {
            fetchBooks(searchInput.value);
        });
    }

    // Initial load fetch
    fetchBooks();
});
