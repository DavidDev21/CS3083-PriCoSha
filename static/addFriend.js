
// handles the submt of friendgroup items
function submitFriendGroup(fgName)
{
    if(fgName)
    {
        let form = document.getElementById('friendForm');
        let firstName = document.getElementsByName('firstName')[0];
        let lastName = document.getElementsByName('lastName')[0];
        if(firstName.value === '' || lastName.value === '')
        {
            alert('Please fill the necessary information');
            return;
        }
        form.action = '/addFriendConfirmation/fg_name=' + fgName;
        form.submit();
        form.reset();
    }
}

document.addEventListener('click', function(e){
    let fgName = e.target.getAttribute('data-fg-name');
    if(fgName)
    {
        submitFriendGroup(fgName);
    }
});