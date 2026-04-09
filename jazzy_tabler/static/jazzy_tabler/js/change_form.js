(function($) {
    'use strict';

    function fixSelectorHeight() {
        $('.selector .selector-chosen').each(function () {
            var selectorChosen = $(this);
            var selectorAvailable = selectorChosen.siblings('.selector-available');
            var selectorChosenSelect = selectorChosen.find('select').first();
            var selectorAvailableSelect = selectorAvailable.find('select').first();
            var selectorAvailableFilter = selectorAvailable.find('p.selector-filter').first();

            selectorChosenSelect.height(selectorAvailableSelect.height() + selectorAvailableFilter.outerHeight());
            selectorChosenSelect.css('border-top', selectorChosenSelect.css('border-bottom'));
        });
    }

    function handleTabs($tabs) {
        var errors = $('.change-form .errorlist li');
        var hash = document.location.hash;

        if (errors.length) {
            var tabId = errors.eq(0).closest('.tab-pane').attr('id');
            $('[data-bs-target="#' + tabId + '"]').tab('show');
        } else if (hash) {
            $('[data-bs-target="' + hash + '"]', $tabs).tab('show');
        }

        $('button[data-bs-toggle="tab"]', $tabs).on('shown.bs.tab', function (e) {
            fixSelectorHeight();
            window.dispatchEvent(new Event('resize'));
            e.preventDefault();
            var target = $(e.target).data('bs-target');
            if (target && history.pushState) {
                history.pushState(null, null, target);
            }
        });
    }

    function handleCollapsible($collapsible) {
        var errors = $('.errorlist li', $collapsible);
        var hash = document.location.hash;

        if (errors.length) {
            $('.accordion-collapse', $collapsible).collapse('hide');
            errors.eq(0).closest('.accordion-collapse').collapse('show');
        } else if (hash) {
            $('.accordion-collapse', $collapsible).collapse('hide');
            $(hash, $collapsible).collapse('show');
        }

        $collapsible.on('shown.bs.collapse', function (e) {
            fixSelectorHeight();
            window.dispatchEvent(new Event('resize'));
            if (history.pushState) {
                history.pushState(null, null, '#' + e.target.id);
            } else {
                location.hash = '#' + e.target.id;
            }
        });
    }

    function applySelect2() {
        var noSelect2 = '.empty-form select, .select2-hidden-accessible, .selectfilter, .selector-available select, .selector-chosen select, select[data-autocomplete-light-function=select2]';
        $('select').not(noSelect2).select2({ width: '100%' });
    }

    $(document).ready(function () {
        var $tabs = $('#content-main form .nav-tabs').first();
        var $collapsible = $('#content-main form #changeform-accordion');

        $('.related-lookup').append('<i class="fa fa-search"></i>');
        $('.inline-related fieldset.module .add-row a').addClass('btn btn-sm btn-outline-secondary float-end');
        $('div.add-row>a').addClass('btn btn-sm btn-outline-secondary float-end');

        if ($tabs.length) { handleTabs($tabs); }
        else if ($collapsible.length) { handleCollapsible($collapsible); }

        applySelect2();

        $('body').on('change', '.related-widget-wrapper select', function(e) {
            var event = $.Event('django:update-related');
            $(this).trigger(event);
            if (!event.isDefaultPrevented() && typeof(window.updateRelatedObjectLinks) !== 'undefined') {
                updateRelatedObjectLinks(this);
            }
        });
    });

    django.jQuery(document).on('formset:added', applySelect2);

})(jQuery);
