
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
    let contentName = document.getElementsByName('contentName')[0];
    let filePath = document.getElementsByName('filePath')[0];
    if(contentName.value === '' || filePath.value === '')
    {
        alert('Please fill the necessary information');
        return;
    }
    form.action = '/processContent/fg_name=public&fg_owner=null';
    form.submit();
    form.reset();
}

// handles the submt of friendgroup items
function submitFriendGroup(e)
{
    let fg_name = e.target.getAttribute('data-fg-name'); 
    let fg_owner = e.target.getAttribute('data-fg-owner');
    if(fg_name && fg_owner)
    {
        let form = document.getElementById('contentForm');

        let contentName = document.getElementsByName('contentName')[0];
        let filePath = document.getElementsByName('filePath')[0];
        if(contentName.value === '' || filePath.value === '')
        {
            alert('Please fill the necessary information');
            return;
        }
        form.action = '/processContent/fg_name=' + fg_name + '&fg_owner=' + fg_owner;
        form.submit();
        form.reset();
    }
}

document.addEventListener('click', submitFriendGroup(e));