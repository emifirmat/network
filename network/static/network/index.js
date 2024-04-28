document.addEventListener('DOMContentLoaded', function() {
    
    // Like and edit post functions
    document.querySelectorAll('.editPost').forEach(function (element) {
        element.addEventListener('click', (event) => editPost(event))
    });
    document.querySelectorAll('.like').forEach(function (element) {
        element.addEventListener('click', (event) => likePost(event))
    });

    
    // Check if user is in its own profile or not
    if (document.querySelector('title').innerHTML === 'Profile') {
        
        const requestuser = document.querySelector('#username').innerHTML
        const profileuser = document.querySelector('#profile-name').innerHTML;
        
        if (profileuser != requestuser) {
            document.querySelector('#follow').addEventListener('click', (event) => 
            update_follow(event));
        };
    }
})
        
function update_follow(event) {

    const csrftoken = getCookie('csrftoken');
    const button = event.target;
    const followersCounter = document.querySelector('#followersCount');
    let counter = parseInt(followersCounter.innerHTML);

    fetch('/follow', {
        method: 'POST',
        headers: {'X-CSRFToken': csrftoken},
        body: JSON.stringify({
            follow: button.innerHTML,
            user_to_follow: button.value
        }),
        mode: 'same-origin'
    })
    .then(response => response.json())
    .then(result => {
        console.log(`${result.message} succesfully.`);
        // Update following button and counter

        if (result.message === 'Following') {
            button.innerHTML = 'Unfollow';
            followersCounter.innerHTML = counter + 1;
            colorAnimation(followersCounter);
        } else {
            button.innerHTML = 'Follow';
            followersCounter.innerHTML = counter - 1;
            colorAnimation(followersCounter);
        };
    });
} 

function editPost(event) {
    // Get tags and content
    const postId = event.target.parentNode.parentNode.parentNode.parentNode.dataset.postid;
    const formTag = document.querySelector(`#form-${postId}`);
    const contentTag = document.querySelector(`#content-${postId}`);
    const content = contentTag.innerHTML;

    // Hide and restart tags
    contentTag.style.display = 'none';
    formTag.innerHTML = '';
    
    // Create form
    const formElement = document.createElement('form');
    formElement.setAttribute('action', '#');
    formElement.setAttribute('method', 'put');

    // Create textarea
    const textAreaElement = document.createElement('textarea');
    textAreaElement.className = "form-control"
    textAreaElement.value = content;

    // Create submit
    const inputElement = document.createElement('input');
    inputElement.className = "btn";
    inputElement.setAttribute('type', 'submit');
    inputElement.setAttribute('value', 'Save');
    inputElement.addEventListener('click', () => {
        event.preventDefault();
        const newContent = textAreaElement.value;
        contentTag.innerHTML = newContent;
        modifyPostContent(newContent, contentTag, postId, formTag, formElement);
    });

    // Include form in DOM
    formElement.append(textAreaElement, inputElement);
    formTag.append(formElement);
    
};

function modifyPostContent(newContent, contentTag, postId, formTag, formElement) {
    const csrftoken = getCookie('csrftoken');
    
    // Update DB in server
    fetch(`/edit_post/${postId}`, {
        method: 'PUT',
        headers: {'X-CSRFToken': csrftoken},
        body: JSON.stringify({
            content: newContent
        }),
        mode: 'same-origin'
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        
        // Update html on Web
        formTag.removeChild(formElement);
        contentTag.style.display = 'block';

        // Show message
        showMessage('edited');
    });
}

function likePost(event) {
    const postId = event.target.parentNode.parentNode.dataset.postid;
    const likesCounter = document.querySelector(`#like-${postId}`)
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/like_post/${postId}`, {
        method: 'POST',
        headers: {'X-CSRFToken': csrftoken},
        mode: 'same-origin'
    })
    .then(response => response.json())
    .then(result => {
        console.log(`Post ${result.message} succesfully.`);
        likesCounter.innerHTML = '❤️' + result.likesCount;
        colorAnimation(likesCounter);

        if (result.message === 'liked') {
            event.target.setAttribute('src', "static/network/dislike.svg");
            event.target.setAttribute('alt', "Unlike");
            event.target.parentNode.children[2].innerHTML = 'Unlike';
        } else {
            event.target.setAttribute('src', "static/network/like.svg");
            event.target.setAttribute('alt', "Like");
            event.target.parentNode.children[2].innerHTML = 'Like';
        }
    })
}

function getCookie(name) {
    // Get cookie for CSRF token
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function colorAnimation(element) {
    // Add color animation
    element.className = "color-anim";
    element.addEventListener('animationend', () => {
        element.classList.remove('color-anim');
    });
}

function showMessage (message) {
    const mDiv = document.querySelector('#post-message');
    mDiv.innerHTML = `The post was ${message} succesfully.`;
    mDiv.className = 'message-anim';
    mDiv.addEventListener('animationend', () => {
        mDiv.classList.remove('message-anim');
        mDiv.innerHTML = "";
    });
}