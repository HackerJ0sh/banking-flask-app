const dropdown = document.getElementById('dropdown');
dropdown.addEventListener('click', function(event) {
    event.preventDefault; 
    console.log('hello world');
    const dropdown_content = document.getElementById('dd-c'); 
    if (dropdown_content.classList.contains('active-dropdown-content')) {
        dropdown_content.classList.remove('active-dropdown-content');
    } else {
        dropdown_content.classList.add('active-dropdown-content');
    }
})

// for the flash message 

function flashCancel() {
    const cancel = document.getElementById('flash-msg-div');
    cancel.style.display = 'none';
}
