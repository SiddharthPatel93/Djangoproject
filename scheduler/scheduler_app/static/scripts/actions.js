function confirmDelete(elem) {
    if(confirm("Are you sure you want to delete this item?")) {
        elem.parentElement.submit();
    }
}

function confirmAdd(elem){
    if(confirm("Are you sure you want to add this TA?")){
        elem.parent.submit();
    }
}