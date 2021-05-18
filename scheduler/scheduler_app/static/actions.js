function confirmAction(elem, msg) {
    if(confirm(`Are you sure you want to ${msg}?`)) {
        elem.parentElement.submit();
    }
}