
// handles actions
function submitAction()
{
    let 
    let form = document.getElementById('contentForm');
    form.action = '/processContent/fg_name=' + fg_name + '&fg_owner=' + fg_owner;
    form.submit();
    form.reset();
}