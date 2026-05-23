'use strict'

$(document).ready(() => {
    const tm = new ThumbmarkJS.Thumbmark()
    tm.get().then(fingerprint => {
        // $('#device_info').val(JSON.stringify({
        //     detector: 'ThumbmarkJS',
        //     fingerprint: fingerprint.thumbmark,
        //     device_info: fingerprint
        // }))
        $('#user_device_id').val('ThumbmarkJS::' + fingerprint.thumbmark)
        console.log('ThumbmarkJS', fingerprint)
        $('#time_zone').val(moment.tz.guess())
    })

    $('body').on('keyup', '.otp-field input', otp_field_keyup)
    $('body').on('click', '#sign-in-request-code', sign_in_request_code)
    $('body').on('click', '#sign-in', sign_in)
})

function otp_field_keyup(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const parent = $($target.parent())

    console.log('$target', $target)
    console.log('parent', parent)
    console.log('e.keyCode', e.keyCode)

    if (e.keyCode === 8 || e.keyCode === 37) {
        const prev = parent.find('input#' + $(this).data('previous'))

        if (prev.length) {
            $(prev).select()
        }
    } else if ((e.keyCode >= 48 && e.keyCode <= 57) || (e.keyCode >= 65 && e.keyCode <= 90) || (e.keyCode >= 96 && e.keyCode <= 105) || e.keyCode === 39) {
        const next = parent.find('input#' + $(this).data('next'))

        if (next.length) {
            $(next).select()
        }
    }

}

function sign_in_request_code(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const $sign_in_request_code_button = $('#sign-in-request-code')
    const $sign_in_button = $('#sign-in')
    const email = $('#email').val()
    const time_zone = $('#time_zone').val()
    const user_device_id = $('#user_device_id').val()
    const email_regex = /^([a-zA-Z0-9_\.\-\+])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/
    const is_email = email_regex.test(email)
    console.log('$target', $target)
    console.log('email', email)
    console.log('is_email', is_email)
    if (!is_email) {
        $('#email').addClass('is-invalid')
        return
    } else {
        $('#email').removeClass('is-invalid')
    }

    $.ajax({
        method: "POST",
        url: `${backend_api_prefix}/auth/sign-in-request-code`,
        contentType: "application/json",
        data: JSON.stringify({
            email: email,
            time_zone: time_zone,
            user_device_id: user_device_id
        }),
        success: (response_data, status, jqxhr) => {
            console.log('success', response_data, status, jqxhr, location)
            $('#request-error').addClass('d-none')
            $('.otp-field').find(':input:disabled').removeAttr('disabled')
            $sign_in_request_code_button.attr('disabled', 'disabled')
            $sign_in_button.removeAttr('disabled')
            $('#otp-field-1').focus()
        },
        error: (jqxhr, status, error) => {
            const error_data = jqxhr.responseJSON
            console.log('error_data', error_data)
            $('#request-error').text(error_data.message).removeClass('d-none')
        }
    })
}

function sign_in(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const $sign_in_button = $('#sign-in')
    const email = $('#email').val()
    const time_zone = $('#time_zone').val()
    const user_device_id = $('#user_device_id').val()
    const codes = []
    $('.otp-field').find(':input').each((idx, el) => { codes.push($(el).val()) })
    const code = codes.join('')
    console.log('sign_in', $target, codes, code)

    $.ajax({
        method: "POST",
        url: `${backend_api_prefix}/auth/sign-in`,
        contentType: "application/json",
        data: JSON.stringify({
            email: email,
            time_zone: time_zone,
            user_device_id: user_device_id,
            code: code
        }),
        success: (response_data, status, jqxhr) => {
            console.log('success', response_data, status, jqxhr, location)
            $('#request-error').addClass('d-none')
            location.href = '/lk/dashboard'
        },
        error: (jqxhr, status, error) => {
            const error_data = jqxhr.responseJSON
            console.log('error_data', error_data)
            $('#request-error').text(error_data.message).removeClass('d-none')
        }
    })
}