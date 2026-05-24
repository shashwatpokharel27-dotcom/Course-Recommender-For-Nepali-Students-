document.addEventListener('DOMContentLoaded', () => {
    // 1. Get the saved data from localStorage
    const courseName = localStorage.getItem('selectedCourse');
    const booksData = localStorage.getItem('courseBooks');
    
    const booksGrid = document.getElementById('books-grid');
    const titleElement = document.getElementById('course-title');

    // 2. Safety check: If someone visits this page directly without clicking a card
    if (!courseName || !booksData) {
        booksGrid.innerHTML = '<p>No course selected. Please go back and select a course.</p>';
        return;
    }

    // 3. Set the page title dynamically
    titleElement.innerText = `Books for ${courseName}`;
    const books = JSON.parse(booksData);

    // 4. Check if there are books in the database for this course
    if (books.length === 0) {
        booksGrid.innerHTML = '<p style="color: var(--text-muted);">No specific books found for this course in our database yet.</p>';
        return;
    }

    // 5. Generate the HTML for each book
    books.forEach(book => {
        const bookCard = document.createElement('div');
        bookCard.className = 'result-card'; // Reusing your beautiful card CSS
        bookCard.style.display = 'flex';
        bookCard.style.flexDirection = 'column';
        bookCard.style.alignItems = 'center';
        bookCard.style.textAlign = 'center';
        bookCard.style.padding = '1rem';

        bookCard.innerHTML = `
            <img src="${book.image}" alt="${book.title}" 
                 style="width: 120px; height: 160px; object-fit: cover; border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" 
                 onerror="this.src='https://via.placeholder.com/120x160?text=No+Cover'">
            <h4 style="font-size: 0.95rem; margin: 0; color: var(--text-main); line-height: 1.3;">${book.title}</h4>
        `;
        booksGrid.appendChild(bookCard);
    });
});