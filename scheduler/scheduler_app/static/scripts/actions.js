function confirmDelete(elem) {
    if(confirm("Are you sure you want to delete this item?")) {
        elem.parentElement.submit();
    }
}