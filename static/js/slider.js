document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    
    sidebar.classList.remove('mobile-show');
    
    mobileMenuToggle.addEventListener('click', function() {
        sidebar.classList.toggle('mobile-show');
        mainContent.classList.toggle('sidebar-open');
    });
    
    document.addEventListener('click', function(event) {
        if (window.innerWidth < 992) {
            const isClickInsideSidebar = sidebar.contains(event.target);
            const isClickOnToggle = mobileMenuToggle.contains(event.target);
            
            if (!isClickInsideSidebar && !isClickOnToggle) {
                sidebar.classList.remove('mobile-show');
                mainContent.classList.remove('sidebar-open');
            }
        }
    });

    // Handle sidebar active state for Change Password and Update Profile
    const sidebarLinks = sidebar.querySelectorAll('.sidebar-menu li a[data-bs-toggle="tab"]');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            sidebarLinks.forEach(l => l.parentElement.classList.remove('active'));
            this.parentElement.classList.add('active');
        });
    });
});