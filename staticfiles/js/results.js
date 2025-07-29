function searchStudents() {
    const searchQuery = document.getElementById('searchInput').value;
    let url = new URL(window.location.href);
    url.searchParams.set('search', searchQuery);  // Set the search query
    window.location.href = url.toString();  // Redirect to the updated URL with search query
}

function printPage() {
    window.print();  // Trigger the print dialog
}