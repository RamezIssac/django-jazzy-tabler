(function($) {
    'use strict';

    function setCookie(key, value) {
        var expires = new Date();
        expires.setTime(expires.getTime() + (365 * 24 * 60 * 60 * 1000));
        document.cookie = key + '=' + value + ';expires=' + expires.toUTCString() + ';SameSite=Strict;path=/';
    }

    function getCookie(key) {
        var keyValue = document.cookie.match('(^|;) ?' + key + '=([^;]*)(;|$)');
        return keyValue ? keyValue[2] : null;
    }

    function handleSidebarToggle() {
        var $toggle = $('#jazzy-sidebar-toggle');
        var $sidebar = $('#jazzy-sidebar');
        var $page = $('.page');

        $toggle.on('click', function(e) {
            e.preventDefault();
            var isCollapsed = $page.hasClass('sidebar-collapsed');
            if (isCollapsed) {
                $page.removeClass('sidebar-collapsed');
                setCookie('jazzy_menu', 'open');
            } else {
                $page.addClass('sidebar-collapsed');
                setCookie('jazzy_menu', 'closed');
            }
        });

        // Restore sidebar state from cookie
        if (getCookie('jazzy_menu') === 'closed') {
            $page.addClass('sidebar-collapsed');
        }
    }

    function setActiveLinks() {
        var url = window.location.pathname;
        var $breadcrumb = $('.breadcrumb a').last();
        var $link = $('a[href="' + url + '"]');
        var $parentLink = $('a[href="' + $breadcrumb.attr('href') + '"]');

        if ($link.length) {
            $link.addClass('active');
        } else if ($parentLink.length) {
            $parentLink.addClass('active');
        }

        // Open parent dropdown if active link is inside one
        var $activeLink = $('a.nav-link.active, a.dropdown-item.active');
        $activeLink.closest('.dropdown').children('.nav-link.dropdown-toggle').addClass('active');
        $activeLink.closest('.dropdown-menu').addClass('show');
    }

    function initDarkModeToggle() {
        var $toggle = $('#jazzy-mode-toggle');
        var $iconDark = $('#jazzy-mode-icon-dark');
        var $iconLight = $('#jazzy-mode-icon-light');

        function updateIcons() {
            var current = document.documentElement.getAttribute('data-bs-theme');
            if (current === 'dark') {
                $iconDark.hide();
                $iconLight.show();
            } else {
                $iconDark.show();
                $iconLight.hide();
            }
        }

        updateIcons();

        $toggle.on('click', function(e) {
            e.preventDefault();
            var current = document.documentElement.getAttribute('data-bs-theme');
            var next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', next);
            var schemeMeta = document.querySelector('meta[name=color-scheme]');
            if (schemeMeta) schemeMeta.setAttribute('content', next);
            localStorage.setItem('jazzy-theme-mode', next);
            updateIcons();
        });
    }

    // Same mechanism as the mode toggle: an attribute on <html> that the head script stores and restores.
    function initSkinChooser() {
        var $choices = $('[data-jazzy-skin-choice]');
        if (!$choices.length || !window.jazzyChooseSkin) return;

        function markActive() {
            var current = document.documentElement.getAttribute('data-jazzy-skin') || '';
            $choices.each(function() {
                var active = $(this).attr('data-jazzy-skin-choice') === current;
                $(this).toggleClass('active', active).attr('aria-pressed', active ? 'true' : 'false');
            });
        }

        markActive();

        $choices.on('click', function() {
            if (window.jazzyChooseSkin($(this).attr('data-jazzy-skin-choice'))) markActive();
        });
    }

    $(document).ready(function() {
        setActiveLinks();
        handleSidebarToggle();
        initDarkModeToggle();
        initSkinChooser();

        // Add table styling to changelist tables that weren't styled
        var $changeListTable = $('#changelist .results table');
        if ($changeListTable.length && !$changeListTable.hasClass('table')) {
            $changeListTable.addClass('table table-striped table-vcenter');
        }
    });

})(jQuery);
