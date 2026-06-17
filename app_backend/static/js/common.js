'use strict'

$(document).ready(() => {
    $('body').on('click', '.modal-open-create', modal_open_create)
    $('body').on('click', '#ModalSubmit', modal_form_submit)
    $('body').on('click', '.form-on-page-submit', form_on_page_submit)
    // $('body').on('click', '.btn[data-bs-toggle="collapse"]', change_collapse_button_icon)
    $('body').on('click', '.filters-wrapper-collapsed', change_collapse_button_icon)
    $('body').on('click', 'table.data-sortable thead tr th[data-sort-col]', table_data_sortable_change_order)
    $('body').on('click', '.list-filter-apply-button', list_filter_apply)
    $('body').on('click', '.list-filter-clear-button', list_filter_clear)
    $('body').on('click', '.grid-pagination .page-item:not(.disabled):not(.active) a.page-link', list_pagination_change_page)
    $('body').on('click', '.grid-pagination .pagination-page-size option', list_pagination_change_page_size)
    $('body').on('click', '.grid-export', list_export)
    $('body').on('click', '.page-grid-export', page_grid_export)
    $('body').on('click', '.code-generate', code_generate)
    $('body').on('click', '.page-filter-apply-button', page_filter_apply)
    $('body').on('click', '.page-filter-clear-button', page_filter_clear)

    // $('.loading-block.not-loaded[data-load-url]').each(load_block_data)

    $("select.select2").select2({
        theme: "bootstrap-5",
    })

    if (!(typeof select2_filters === 'undefined') && (Object.keys(select2_filters).length > 0)) {
        for(let key in select2_filters) {
            if (select2_filters.hasOwnProperty(key)) {
                $('#' + key).val(select2_filters[key])
                $('#' + key).trigger('change')
            }
        }
    }

    const grid_tables = $('.grid-wrapper .grid-table table')
    if (grid_tables.length > 0) {
        for (const grid_table of grid_tables) {
            if ($(grid_table).data('load-url')) {
                load_grid_table_data(grid_table, 1)
            }
        }
    }

    const loading_blocks = $('.loading-block.not-loaded[data-load-url]')
    if (loading_blocks.length > 0) {
        for (const loading_block of loading_blocks) {
            console.log('ready', 'loading_block', loading_block)
            load_block_data(0, loading_block)
        }
    }
})

function load_block_data(idx, el) {
    const $el = $(el)
    const url = $el.data('load-url')
    console.log('load_block_data', idx, el, url)
    $.ajax({
        url: url,
        type: 'GET',
        // dataType: 'json',
        // beforeSend: (jqxhr, settings) => {
        //     $grid_loader.removeClass('d-none')
        // },
        complete: (jqxhr, status) => {
            // $grid_loader.addClass('d-none')
            $el.removeClass('not-loaded').addClass('loaded')
        },
        success: (response_data, status, jqxhr) => {
            // console.log('success', response_data, status, jqxhr, location)
            $el.html(response_data)
            // $table_body.empty().append(response_data.body)
            // $grid_pagination.empty().append(response_data.pagination)
            // $table.data('order', response_data.order)
            // $table.data('direction', response_data.direction)
            // $table.data('total', response_data.total)
            // table_data_sortable_update_header(0, el)
        },
        error: (jqxhr, status, error) => {
            // const error_data = jqxhr.responseJSON
            // console.log('error', jqxhr, status, error, error_data)
            console.log('error', jqxhr, status, error)
            // $grid_alert.text(error_data.message).removeClass('d-none')
        }
    })
}

function get_grid_table_load_url_params(el, page, is_export) {
    const $table = $(el)
    const $grid_wrapper = $($table.parents('.grid-wrapper')[0])
    const $table_filters = $($grid_wrapper.find('.grid-filters')[0])
    const $grid_pagination = $($grid_wrapper.find('.grid-pagination')[0])
    const direction = $table.data('sort-direction')
    const order = $table.data('sort-col')
    const page_sizes = $grid_pagination.find('.pagination-page-size')
    const limit = $table.data('limit') || page_sizes.length > 0 ? parseInt($table.data('limit') || $(page_sizes[0]).val()) : 10

    // console.log('get_grid_table_load_url_params', $table, $grid_wrapper, $table_filters, $table, $grid_pagination)
    // console.log('get_grid_table_load_url_params', direction, order, page)

    if (!page) {
        const page_links = $grid_pagination.find('.page-item.active a.page-link')
        page = page_links.length > 0 ? $(page_links[0]).data('page') : 1
        // console.log('get_grid_table_load_url_params', page_links, page)
    }

    let params = {page: page, limit: limit, is_export: is_export}

    if (order && direction) {
        params['sort'] = (direction == 'down' ? '-' : '') + order
    }

    $table_filters.find('.list-filter select[data-filter], .list-filter input[data-filter], .list-filter :checked[data-filter]').each(function () {
        const filterField = this.dataset.filter
        if ($(this).is('input')) {
            // Для input элементов (например, date, text search) берем значение
            const inputValue = this.value || ''
            // Для текстового поиска (query_text) не отправляем пустые значения
            // Для дат отправляем даже пустые значения, чтобы сбросить фильтр
            if (filterField === 'query_text') {
                // Для текстового поиска отправляем только непустые значения
                if (inputValue && inputValue.trim() && inputValue.toLowerCase() !== 'none') {
                    params[filterField] = inputValue.trim()
                }
            } else {
                // Для дат отправляем значение (может быть пустым для сброса фильтра)
                params[filterField] = inputValue
            }
        } else if ($(this).hasClass('select2') && $(this).prop('multiple')) {
            if (!$(this).val().length) {
                params[this.dataset.filter] =  ''
            } else {
                params[this.dataset.filter] = []
                for (let i = 0; i < $(this).val().length; i++) {
                    params[this.dataset.filter].push($(this).val()[i])
                }
            }
        } else {
            const selectValue = this.value
            // Для select отправляем значение (пустая строка для сброса фильтра)
            // Но не отправляем строку "None"
            if (selectValue && selectValue.toLowerCase() !== 'none') {
                params[this.dataset.filter] = selectValue
            } else if (!selectValue) {
                params[this.dataset.filter] = ''
            }
        }
    })

    return params
}

function load_grid_table_data(el, page, is_export=false) {
    const $table = $(el)
    const url = new URL($table.data('load-url'))
    const $table_body = $($table.find('tbody')[0])
    const $grid_wrapper = $($table.parents('.grid-wrapper')[0])
    const $grid_loader = $($grid_wrapper.find('.grid-loader')[0])
    const $grid_alert = $($grid_wrapper.find('.grid-alert')[0])
    const $grid_pagination = $($grid_wrapper.find('.grid-pagination')[0])
    const params = get_grid_table_load_url_params(el, page, is_export)

    for (const key in params) {
        if (Array.isArray(params[key])) {
            for (let i = 0; i < params[key].length; i++) {
                url.searchParams.append(key, params[key][i])
            }
        } else {
            url.searchParams.append(key, params[key])
        }
    }

    // console.log('load_grid_table_data', $table, url, $grid_wrapper, $table_body, $grid_pagination, params, url)
    if (is_export) {
        $.ajax({
            url: url,
            type: 'GET',
            dataType: 'binary',
            xhrFields: {
                'responseType': 'blob'
            },
            success: (response_data, status, jqxhr) => {
                const link = document.createElement('a')
                link.style = "display: none"
                link.href = URL.createObjectURL(response_data)
                // link.download = filename
                link.click()
            },
            error: (jqxhr, status, error) => {
                // console.log('error', jqxhr, status, error, error_data)
                handleError({status: jqxhr.status.code, message: error})
            }
        })
    } else {
        $.ajax({
            url: url,
            type: 'GET',
            dataType: 'json',
            beforeSend: (jqxhr, settings) => {
                $grid_loader.removeClass('d-none')
            },
            complete: (jqxhr, status) => {
                $grid_loader.addClass('d-none')
            },
            success: (response_data, status, jqxhr) => {
                // console.log('success', response_data, status, jqxhr, location)
                $table_body.empty().append(response_data.body)
                $grid_pagination.empty().append(response_data.pagination)
                $table.data('order', response_data.order)
                $table.data('direction', response_data.direction)
                $table.data('total', response_data.total)
                table_data_sortable_update_header(0, el)
            },
            error: (jqxhr, status, error) => {
                const error_data = jqxhr.responseJSON
                console.log('error', jqxhr, status, error, error_data)
                $grid_alert.text(error_data.message).removeClass('d-none')
            }
        })
    }
}

function modal_open_create(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const $close = $('#ModalClose')
    const $submit = $('#ModalSubmit')
    const url = $target.data('url')
    const submit_url = $target.data('submit-url')
    const index_url = $target.data('index-url')
    const index_url_with_id = $target.data('index-url-with-id')
    const modal_header = $target.data('modal-header')
    const modal_body = $target.data('modal-body')
    const loading_block = $target.parents('.loading-block')

    console.log('modal_open_create', e, $target, loading_block)

    $submit.data('url', submit_url || url)
    $submit.data('index-url', index_url)
    $submit.data('index-url-with-id', index_url_with_id)
    $submit.data('loading-block', loading_block.length ? loading_block[0] : null)

    if ($target.hasClass('delete-object')) {
        $('#Modal .modal-content .modal-header .modal-title').text(modal_header)
        $('#Modal .modal-content .modal-body').html(modal_body)
        $submit.removeClass('d-none')
        $submit.text('Удалить')
        $submit.data('method', 'DELETE')
        $close.text('Отменить')
        $('#Modal').modal('show')
    } else if ($target.hasClass('view-object')) {
        $('#Modal .modal-content .modal-header .modal-title').text(modal_header)
        $('#Modal .modal-content .modal-body').html(modal_body)
        $submit.addClass('d-none')
        $close.text('Закрыть')
        $('#Modal').modal('show')
    } else {
        $.get(url, (data) => {
            $('#Modal .modal-content .modal-header .modal-title').text(modal_header)
            $('#Modal .modal-content .modal-body').html(data)
            $submit.removeClass('d-none')
            $submit.text('Сохранить')
            $submit.data('method', $target.hasClass('create-object') ? 'POST' : 'PUT')
            $close.text('Отменить')
            $('#Modal').modal('show')
        })
    }
}

function modal_form_submit(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const url = $target.data('url')
    const index_url = $target.data('index-url')
    const index_url_with_id = $target.data('index-url-with-id')
    // const loading_block = $target.parents('.loading-block')
    const loading_block = $target.data('loading-block')
    const method = $target.data('method')
    const $form = $('#Modal .modal-content .modal-body form')
    const $alert = $('#Modal .modal-content .modal-body .alert')
    const $disabled = $form.find(':input:disabled').removeAttr('disabled')
    const data = (method != 'DELETE') ? $form.serialize() : null
    $disabled.attr('disabled', 'disabled')
    console.log('modal_form_submit', e, $target, loading_block)
    // console.log('modal_form_submit', index_url, url, method, data, e)
    // console.log('modal_form_submit', 'JQuery version=' + $.fn.jquery)

    $.ajax({
        url: url,
        data: data,
        type: method,
        dataType: 'json',
        success: (response_data, status, jqxhr) => {
            // console.log('success', response_data, status, jqxhr, location)
            $('#Modal').modal('hide')

            // Если есть родительский блок `.loading-block`, то выполняем загрузку данных блока
            // if (loading_block.length) {
            if (loading_block) {
                // load_block_data(0, loading_block[0])
                load_block_data(0, loading_block)
            } else if (index_url_with_id) {
                const response_id = response_data.id
                const redirect_url = new URL(index_url, window.location.origin)
                if (response_id) {
                    redirect_url.searchParams.append('id', response_id)
                }
                location.href = redirect_url.toString()
            } else {
                location.href = index_url
            }
        },
        error: (jqxhr, status, error) => {
            // console.log('error', jqxhr, status, error)
            const error_data = jqxhr.responseJSON
            if (error_data) {
                const obj = error_data.data
                $alert.text(error_data.message).removeClass('d-none')
                $('#Modal .modal-content .modal-body .invalid-feedback').remove()
                $('#Modal .modal-content .modal-body .is-invalid').removeClass('is-invalid')
                for (const key in obj) {
                    if (obj.hasOwnProperty(key)) {
                        const value = Array.isArray(obj[key]) ? obj[key][[obj[key].length - 1]] : obj[key]
                        $('<div id="' + key + '-feedback" class="invalid-feedback">' + value + '</div>').insertAfter('#Modal .modal-content .modal-body #' + key)
                        $('#Modal .modal-content .modal-body #' + key).addClass('is-invalid')
                    }
                }
            }
        }
    })
}

function change_collapse_button_icon(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const parent_class = $target.data('target-parent-class')
    const wrapper_class = $target.data('target-class')
    const parents = $target.parents('.' + parent_class)
    // console.log('change_collapse_button_icon', $target, parent_class, wrapper_class, parents)

    if (parents.length) {
        $(parents[0]).find('.' + wrapper_class).toggleClass('d-none')
        $target.find('i').toggleClass('d-none')
    }
}

function copy_to_clipboard(text_to_copy) {
    navigator.clipboard.writeText(text_to_copy)
}

function table_data_sortable_update_header(idx, el) {
    const $el = $(el)
    const order = $el.data('sort-col')
    const direction = $el.data('sort-direction')
    const old_direction = direction == 'down' ? 'up' : 'down'
    const total = $el.data('total')
    const col = $el.find('thead tr th[data-sort-col=' + order + ']')
    // console.log('table_data_sortable_update_header', idx, el, $el, order, direction, old_direction, col)

    $el.find('thead tr th[data-sort-col] i.bi').remove()

    if (col.length && total) {
        const col_icon = $(col[0]).find('i.bi')
        if (col_icon.length) {
            const $col_icon = $(col_icon[0])
            if (!$col_icon.hasClass('bi-sort-' + direction)) {
                $col_icon.removeClass('bi-sort-' + old_direction).addClass('bi-sort-' + direction)
            }
        } else {
            $(col).append('<i class="bi bi-sort-' + direction + ' ms-2"></i>')
        }
    }
}

function table_data_sortable_change_order(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const col = $target.data('sort-col')
    const $table = $target.parents('table')
    const direction = $table.data('sort-direction')
    const order = $table.data('sort-col')
    const total = $table.data('total')
    // console.log('table_data_sortable_change_order', col, direction, order, total)
    if (total) {
        if (order != col) {
            $table.data('sort-col', col)
        } else {
            $table.data('sort-direction', direction == 'down' ? 'up' : 'down')
        }

        load_grid_table_data($table)
    }
}

function list_pagination_change_page(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const page = $target.data("page")
    const $grid_wrapper = $($target.parents('.grid-wrapper')[0])
    const $table = $($grid_wrapper.find('.grid-table table')[0])

    load_grid_table_data($table, page)
}

function list_pagination_change_page_size(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const $grid_wrapper = $($target.parents('.grid-wrapper')[0])
    const $table = $($grid_wrapper.find('.grid-table table')[0])

    load_grid_table_data($table, 1)
}

function list_export(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const $list_page_wrapper = $($target.parents('.list-page-wrapper')[0])
    const $grid_wrapper = $($list_page_wrapper.find('.grid-wrapper')[0])
    const $table = $($grid_wrapper.find('.grid-table table')[0])
    // console.log('list_export', $target, $list_page_wrapper, $grid_wrapper, $table)

    load_grid_table_data($table, 1, true)
}

function list_filter_apply(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const $grid_wrapper = $($target.parents('.grid-wrapper')[0])
    const $table = $($grid_wrapper.find('.grid-table table')[0])
    // console.log('list_filter_apply', $grid_wrapper, $table)

    load_grid_table_data($table, 1)
}

function list_filter_clear(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const $grid_wrapper = $($target.parents('.grid-wrapper')[0])
    const $table = $($grid_wrapper.find('.grid-table table')[0])

    $grid_wrapper.find('.list-filter select[data-filter], .list-filter input[data-filter], .list-filter :checked[data-filter]').each(function () {
        if ($(this).is('input')) {
            $(this).val('')
        } else {
            $(this).val(null).trigger('change')
        }
    })

    // console.log('list_filter_clear', url, $grid_wrapper, $table)
    load_grid_table_data($table, 1)
}

function form_on_page_submit(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const url = $target.data('url')
    const $form = $('.form-on-page-wrapper form.form-on-page')
    const $alert_danger = $('.form-on-page-wrapper .alert-danger')
    const $alert_success = $('.form-on-page-wrapper .alert-success')
    const $loader = $('.form-on-page-loade')
    const $disabled = $form.find(':input:disabled').removeAttr('disabled')
    const data = $form.serialize()
    $disabled.attr('disabled', 'disabled')
    // console.log('form_on_page_submit', index_url, url, method, data, e, $.fn.jquery)
    // console.log('form_on_page_submit', 'JQuery version=' + $.fn.jquery)

    $.ajax({
        url: url,
        data: data,
        type: 'PUT',
        dataType: 'json',
        beforeSend: (jqxhr, settings) => {
            $loader.removeClass('d-none')
        },
        complete: (jqxhr, status) => {
            $loader.addClass('d-none')
        },
        success: (response_data, status, jqxhr) => {
            // console.log('success', response_data, status, jqxhr, location)
            $alert_success.removeClass('d-none')
            $alert_danger.addClass('d-none')
        },
        error: (jqxhr, status, error) => {
            // console.log('error', jqxhr, status, error)
            $alert_success.addClass('d-none')
            const error_data = jqxhr.responseJSON
            if (error_data) {
                const obj = error_data.data
                $alert_danger.text(error_data.message).removeClass('d-none')
                $('.form-on-page-wrapper .invalid-feedback').remove()
                $('.form-on-page-wrapper .is-invalid').removeClass('is-invalid')
                for (const key in obj) {
                    if (obj.hasOwnProperty(key)) {
                        const value = Array.isArray(obj[key]) ? obj[key][[obj[key].length - 1]] : obj[key]
                        $('<div id="' + key + '-feedback" class="invalid-feedback">' + value + '</div>').insertAfter('.form-on-page-wrapper #' + key)
                        $('.form-on-page-wrapper #' + key).addClass('is-invalid')
                    }
                }
            }
        }
    })
}

function add_code_generate_input_addons(
    element_id,
    button_url,
    code_length,
    as_uuid = false,
    as_base64 = false,
    button_title = 'Сгенерировать код автоматически',
    button_position = 'before',
    button_icon_class = 'bi-lightning-charge',
    button_class = 'code-generate'
) {
    if (!button_url && !code_length && !as_uuid) {
        return
    }

    const $label = $('label[for="' + element_id + '"]')
    const $input = $('#' + element_id)
    const $parent = $input.parent('div')
    $label.addClass('input-group')
    $parent.addClass('input-group')
    const $button = $('<i/>')
        .attr('class', 'bi ' + button_icon_class + ' input-group-text ' + button_class)
        .attr('title', button_title)
        .attr('data-input-id', element_id)

    if (code_length) {
        $button.data('code-length', code_length)
    }

    if (button_url) {
        $button.data('url', button_url)
    }

    if (as_uuid) {
        $button.data('as-uuid', as_uuid)
    }

    if (as_base64) {
        $button.data('as-base64', as_base64)
    }

    if (button_position == 'before') {
        $button.insertBefore($input)
    } else {
        $button.insertAfter($input)
    }
}

function code_generate(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const input_id = $target.data('input-id')
    const $input = $('#' + input_id)
    const url = $target.data('url')
    const code_length = $target.data('code-length')
    const as_uuid = $target.data('as-uuid')
    const as_base64 = $target.data('as-base64')

    if (code_length) {
        // const code = btoa(Math.random()).slice(0, code_length)
        const code = generate_random_string(code_length)
        $input.val(as_base64 ? btoa(code) : code)
        return
    }

    if (as_uuid) {
        const code = $.uuid()
        $input.val(as_base64 ? btoa(code) : code)
        return
    }

    if (url) {
        $.ajax({
            url: url,
            type: 'GET',
            dataType: 'json',
        })
            .done((response_data) => {
                if (response_data.code) {
                    $input.val(response_data.code)
                }
            })
    }
}

function generate_random_string(string_length, is_uppercase = false) {
    let random_string = ''
    let characters = '0123456789abcdefghijklmnopqrstuvwxyz'
    if (is_uppercase) {
        characters += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    }
    for (let i = 0; i < string_length; i++) {
        const randomInd = Math.floor(Math.random() * characters.length);
        random_string += characters.charAt(randomInd);
    }
    console.log(is_uppercase, characters, random_string)
    return random_string
}

function page_filter_apply(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const $grid_wrapper = $($target.parents('.grid-wrapper')[0])
    const $table_filters = $($grid_wrapper.find('.grid-filters')[0])

    // console.log('page_filter_apply', $target, $table_filters)
    page_reload($table_filters, false)
}

function page_reload($table_filters, is_export = false) {
    const url = new URL(location.href.split('?')[0])
    let params = {is_export: is_export}

    $table_filters.find('.list-filter select[data-filter], .list-filter :checked[data-filter], .list-filter input[data-filter]').each(function () {
        // console.log('$table_filters.find', $(this), $(this).hasClass('sel2'), $(this).prop('multiple'))
        if ($(this).hasClass('sel2') && $(this).prop('multiple')) {
            if (!$(this).val().length) {
                params[this.dataset.filter] =  ''
            } else {
                params[this.dataset.filter] = []
                for (let i = 0; i < $(this).val().length; i++) {
                    params[this.dataset.filter].push($(this).val()[i])
                }
            }
        } else {
            params[this.dataset.filter] = this.value
        }
    })

    // console.log('page_reload', params)
    for (const key in params) {
        if (Array.isArray(params[key])) {
            for (let i = 0; i < params[key].length; i++) {
                url.searchParams.append(key, params[key][i])
            }
        } else {
            url.searchParams.append(key, params[key])
        }
    }

    // console.log('page_reload', params, url)
    location.href = url
}

function page_filter_clear(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const url = new URL(location.href.split('?')[0])
    location.href = url
}

function page_grid_export(e) {
    e.preventDefault()
    e.stopImmediatePropagation()

    const $target = $(e.currentTarget)
    const $list_page_wrapper = $($target.parents('.list-page-wrapper')[0])
    const $grid_wrapper = $($list_page_wrapper.find('.grid-wrapper')[0])
    const $table_filters = $($grid_wrapper.find('.grid-filters')[0])

    // console.log('page_grid_export', $target, $table_filters)
    page_reload($table_filters, true)
}
