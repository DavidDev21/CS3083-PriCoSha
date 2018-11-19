
// toggle the friendgroup table
function toggleFriendGroup()
{
    let fg_table = document.getElementById('FriendGroupTable')
    let publicBtn = document.getElementById('publicSubmit');
    if(fg_table.style.display === 'none')
    {
        fg_table.style.display = 'block';
        publicBtn.style.display = 'none';
    }
    else
    {
        fg_table.style.display = 'none';
        publicBtn.style.display = 'block';
    }
}

// handles the submit of public items
// note fg_owner value plays no role here. It's just to get to the correct route
function submitPublic()
{
    let form = document.getElementById('contentForm');
    form.action = '/processContent/fg_name=public&fg_owner=null';
    form.submit();
    form.reset();
}

// handles the submt of friendgroup items
function submitFriendGroup()
{
    let form = document.getElementById('contentForm');
    let fg_name = $('#friendGroupSubmit').data()['fgName']; 
    let fg_owner = $('#friendGroupSubmit').data()['fgOwner'];
    form.action = '/processContent/fg_name=' + fg_name + '&fg_owner=' + fg_owner;
    form.submit();
    form.reset();
}