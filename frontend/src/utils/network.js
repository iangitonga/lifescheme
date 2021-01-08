
/**
 * Retrieves a cookie from @name if it is found else `null` is returned.
 * */
const getCookie = (name) => {
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
};


/**
 * Sends a POST request using the given data to the given endpoint.
 * @param endpoint string a url to send the request to.
 *
 *
 * @param data an object containing the payload to be sent to the
 * endpoint.
 *
 * @param successCbc a function that accepts one argument to be called with the
 * response data when the request status response is 200.
 *
 * @param errorCbc a function that accepts one argument to be called with the
 * response data when the request status response is 400 and has form errors.
 *
 * @param failureCbc a function that accepts no argument to be called when the
 * response neither is 200 nor has form errors.
 *
 * @param postSendCbc an optional function that accepts no arguments to be
 * called after the data has been sent and response received. This callback
 * will be called before any other callbacks.
 *
 * @return null.
 * */
const post = (endpoint, data, successCbc, errorCbc, failureCbc, postSendCbc) => {
    // Prepare the data to be sent.
    const formDataEncoded = new FormData();
    formDataEncoded.append('csrfmiddlewaretoken', getCookie('csrftoken'));
    for (const key in data) {
        if (!data.hasOwnProperty(key)) {continue;}
        formDataEncoded.append(key, data[key]);
    }

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: formDataEncoded,
        mode: 'no-cors',
    })
    .then((response) => {
        if (postSendCbc)
            postSendCbc();
        if (response.status === 200) {
            response.json().then((jsonResponse) => {
                successCbc(jsonResponse);
            });
        }
        else {
            response.json().then(jsonResponse => {
                if (response.status === 400 && jsonResponse['FORM_ERRORS']) {
                    errorCbc(jsonResponse['FORM_ERRORS']);
                } else {
                    console.log(`Error: ${jsonResponse}`);
                    failureCbc();
                }
            }).catch((error) => {
                console.log(`Error: ${error}`);
                failureCbc();
            });
        }
    })
    .catch((error) => {
        if (postSendCbc)
            postSendCbc();
        console.log(`Error: ${error}`);
        failureCbc();
    });
};


export default post;
