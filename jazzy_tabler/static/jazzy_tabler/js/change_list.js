(function($) {
    'use strict';

    $.fn.search_filters = function () {
        $(this).change(function () {
            var $field = $(this);
            var $option = $field.find('option:selected');
            var select_name = $option.data('name');
            if (select_name) {
                $field.attr('name', select_name);
            } else {
                $field.removeAttr('name');
            }
        });
        $(this).trigger('change');
    };

    function getMinimumInputLength(element) {
        return window.filterInputLength[element.data('name')] ?? window.filterInputLengthDefault;
    }

    function searchFilters() {
        var $ele = $('.search-filter');
        $ele.search_filters();
        $ele.each(function () {
            var $this = $(this);
            $this.select2({ minimumInputLength: getMinimumInputLength($this) });
        });

        var $mptt = $('.search-filter-mptt');
        if ($mptt.length) {
            $mptt.search_filters();
            $mptt.select2({
                minimumInputLength: getMinimumInputLength($mptt),
                templateResult: function (data) {
                    if (!data.element) {
                        return data.text;
                    }
                    var $element = $(data.element);
                    var $wrapper = $('<span></span>');
                    $wrapper.attr('style', $($element[0]).attr('style'));
                    $wrapper.text(data.text);
                    return $wrapper;
                },
            });
        }
    }

    $(document).ready(function () {
        $('.related-lookup').append('<i class="fa fa-search"></i>');
        $('.actions select').addClass('form-select').select2({ width: 'element' });
        searchFilters();
    });

})(jQuery);
