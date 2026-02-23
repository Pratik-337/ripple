function loadUsers() {
    fetch("/users")
        .then(res => res.text())
        .then(data => console.log(data));
}
