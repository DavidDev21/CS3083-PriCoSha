
function toggleFriendGroup()
{
    let fg_table = document.querySelectorAll('.friend-group');
    let pg_table = document.querySelectorAll('.public-group');
    let publicForm = document.getElementById('publicForm');
    let publicBtn = document.getElementById('publicSubmit');
    for(let i = 0; i < fg_table.length; i++)
    {
        if(fg_table[i].style.display === 'none')
        {
            fg_table[i].style.display = 'block';
            publicForm.style.display = 'none'
            publicBtn.style.display = 'none';
        }
        else
        {
            fg_table[i].style.display = 'none';
            publicForm.style.display = 'block';
            publicBtn.style.display = 'block';
        }
    }
}
function submitPublic()
{
    let form = document.getElementById('postPublic');
    form.action = '/processPublicContent/fg_name=public';
    $('#postContentForm').submit();
    $('#postContentForm').reset();
}

function submitFriendGroup()
{
    console.log($('#fg_name').data('data-target'));
    $('#postContentForm').action = '/processContent/fg_name=' + $('#fg_name').data('data-target');
    $('#postContentForm').submit();
    $('#postContentForm').reset();
}