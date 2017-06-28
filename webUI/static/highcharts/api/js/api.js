var $hilighted,
    $hilightedMenuItem,
    optionDictionary = {},
    names = [],
    buildApiOffline,
    offline = {},
    API = {},
    methods = [],
    memberInfo = {},
    usedUrls = [],
    page = PAGE,
    buildPage;

function loadScript(url, callback) {
    //http://www.nczonline.net/blog/2009/07/28/the-best-way-to-load-external-javascript/
    var script = document.createElement("script");
    script.type = "text/javascript";
    if (script.readyState) {  //IE
        script.onreadystatechange = function () {
            if (script.readyState == "loaded" ||
                script.readyState == "complete") {
                script.onreadystatechange = null;
                callback();
            }
        };
    } else {  //Others
        script.onload = function () {
            callback();
        };
    }

    script.src = url;
    document.getElementsByTagName("head")[0].appendChild(script);
}

function toDot(id) {
    return id.replace(/[-]+/g, '.');
}

function escapeHTML(html) {
    if (typeof html === 'string') {
        html = html
            .replace('\u25CF', '\\u25CF')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }
    return html;
}

function escapeSelector(name) {
    return name.replace('<', '\\<').replace('>', '\\>');
}

function activateInternalLinks($parent) {
    $('a[href^="#"]', $parent).each(function (i, anchor) {
        $(anchor).click(function (e) {
            memberClick(anchor.href.replace(/.*#/, ''), e);
            return false;
        });
    });
}


/**
 * Highligth a specific option by coloring it in the menu view and section view
 */
function hilight(id) {
    var linkId, $el, $detailsWrap = $('#details-wrap');

    $el = $('div.member#' + escapeSelector(id));

    // clear old
    if ($hilighted) {
        $hilighted.removeClass('hilighted');
    }
    if ($hilightedMenuItem) {
        $hilightedMenuItem.removeClass('hilighted');
    }

    if ($el.length === 0) {
        $detailsWrap.scrollTop(0);
    } else {
        // hilight new
        $hilighted = $el;
        $hilighted.addClass('hilighted');

        // Scroll to the hilighted member
        $detailsWrap.animate({scrollTop: $hilighted.offset().top + $detailsWrap.scrollTop() - 160}, 400);

        // Workaround for weird case where an element wont scroll under certain conditions
        // http://stackoverflow.com/questions/1830080/jquery-scrolltop-doesnt-seem-to-work-in-safari-or-chrome-windows#answer-4165094
        $('body, html, document').animate({scrollTop: $hilighted.offset().top + $detailsWrap.scrollTop() - 160}, 400);
    }
    linkId = id.replace(/[^a-z0-9<>\\]+/gi, '.');

    $hilightedMenuItem = $('a[href="/' + getBasePath() + linkId + '"]').not('.plus');
    $hilightedMenuItem.addClass('hilighted');

}

/**
 * Expand and load children when necessary of current level
 */
function toggleExpand($elem, callback) {
    var $_menu = $elem.find('div[id$="-menu"]').first(),
        _id = $_menu.attr('id').replace("-menu", ""),
        displayChildrenCallback = function () {

            $('.dots', $elem).removeClass('loading');
            $elem.removeClass("collapsed");
            $elem.addClass("expanded");
            $_menu.slideDown();
            // show relevant section

            if (/[A-Z]/.test(_id[0])) {
                _id = 'object-' + _id;
            }
            toggleSection(_id);

            if (callback) {
                callback();
            }

        };


    if ($elem.hasClass('collapsed')) {

        /* if not loaded, load children, standard we have three children */
        if ($_menu.children().size() == 1) {
            $('.dots', $elem).addClass('loading');
            loadChildren(_id, false, displayChildrenCallback);

        } else {
            displayChildrenCallback();
        }
    } else {
        // hide children
        $_menu.slideUp('normal', function () {
            $elem.removeClass("expanded");
            $elem.addClass("collapsed");
        });
    }
}

function toggleSection(sectionId) {
    $section = $("#details > div.section:visible");

    // hide current section
    if ($section) {
        $section.hide();
    }
    if (/[^\\]</.test(sectionId)) {
        sectionId = sectionId.replace('<', '\\<').replace('>', '\\>');
    }
    $('#details > div.section#' + sectionId).show();
}

/**
 * Makes a member name with dot-notation wrappable as html by splitting it at the dots and returning spans with text
 *
 * @param memberTitle - the dot-notation member title
 */
function wrappableMemberTitle(memberTitle) {
    var parts = memberTitle.split('.'),
        wrappableMemberTitle = '',
        index;
    for (index in parts) {
        wrappableMemberTitle += '<span>.' + parts[index] + '</span>';
    }

    // Replace first dot
    wrappableMemberTitle = wrappableMemberTitle.replace(/\./, '');

    return wrappableMemberTitle;
}

function addSectionOption(val) {
    var title = val.fullname.replace('<', '&lt;').replace('>', '&gt;');
    $section = $('<div class="section" id="' + val.name + '" style="display:none;"></div>').appendTo('#details');
    $('<h1>' + wrappableMemberTitle(title) + '</h1>'
        + (val.description ? '<div class="section-description">' + val.description + '</div>' : '')
        + (val.demo ? '<div class="demo section-demo"><h4>Try it:</h4> ' + val.demo + '</div>' : '' )).appendTo($section);

    activateInternalLinks($section);
    $(document).triggerHandler({type: "xtra.btn.section.event", id: optionDictionary[val.fullname], table: 'option'});
}

function addSectionObject(val) {
    var title = val.title;
    $section = $('<div class="section" id="object-' + val.name + '" style="display:none;"></div>').appendTo('#details');
    $('<h1>' + wrappableMemberTitle(title) + '</h1>').appendTo($section);
    $('<div class="section-description">' + val.description + '</div>').appendTo($section);

    activateInternalLinks($section);
    $(document).triggerHandler({type: "xtra.btn.section.event", id: 'object-' + val.name, table: 'object'});
}

function markupReturnType(s) {
    var basePath;
    if (historyEnabled()) {
        basePath = '/' + getBasePath();
    } else {
        basePath = '#';
    }
    s = s.replace(/[<>]/g, function (a) {
        return {
            '<': '&lt;',
            '>': '&gt;'
        }[a];
    });
    s = s.replace(/(Axis|Chart|Element|Highcharts|Point|Renderer|Series)/g, '<a href="' + basePath + '$1">$1</a>');
    return s;
}

/**
 * Checks if the history API
 * @returns {boolean}
 */
function historyEnabled() {
    return runDB &&
        window.history !== undefined &&
        window.history !== null &&
        window.history.pushState !== undefined &&
        window.history.pushState !== null;
}

/**
 * Makes info about a member available at the memberInfo map for e.g. rich cards.
 *
 * @param memberObject - an object containing information about a member
 */
function storeMember(memberObject) {
    // Add a pretty name with '()' if the member is a method
    memberObject.prettyName = memberObject.fullname + (memberObject.type === 'method' ? '()' : '');

    // Add the member to the memberInfo map with the dot-notation name
    memberInfo[memberObject.fullname] = memberObject;
}

/**
 * Creates a script element for the Google Rich Card and returns it as a jQuery object.
 *
 * @returns {*|jQuery|HTMLElement} the Google Rich Card script as a jQuery object
 */
function addRichCardScript() {
    var script = document.createElement("script");

    script.id = "richCard";
    script.type = "application/ld+json";

    document.getElementsByTagName("head")[0].appendChild(script);

    return $(script);
}

/**
 * Returns the memberInfo of a specific member, or an empty object if it does not exist.
 *
 * @param {string} member - the member id to get info from (dot-notation)
 * @returns {object} the memberInfo of a specific member, or an empty object if it does not exist
 */
function getMemberInfo(member) {
    return memberInfo[member] ? memberInfo[member] : {};
}

/**
 * Modifies or creates the Google Rich Card with information from the member.
 *
 * If the card does not exist, it is created via addRichCardScript().
 *
 * @param member - the id of the member (dot-notation)
 */
function modifyRichCard(member) {
    var cardScript = $('#richCard'),
        json = {
            "@context": "http://schema.org/",
            "@type": "APIReference",
            "name": member,
            "image": "http://api.highcharts.com/resources/images/" + PRODUCTNAME + ".svg",
            "description": getMemberInfo(member).description
        };

    if (cardScript.length < 1) {
        cardScript = addRichCardScript();
    }

    cardScript.html(JSON.stringify(json, null, 4));
}

/**
 * Updates the height of the nav and wrapper.
 */
function updateHeight() {
    var $wrapper = $("#wrapper"),
        $wrapperContainer = $("#wrapper .container");
    if (jQuery(window).width() >= 768) {
        // Disable
        var padding,
            height = $(window).height() - $('#top').height() - $('#footer').height();
        $wrapper.height(height);
        padding = $wrapperContainer.innerHeight() - $wrapperContainer.height();
        height = $wrapper.height() - padding;
        $("#wrapper-inner").height(height);
        $("#nav-wrap").height(height);
        $("#details-wrap").height(height);
    } else {
        // no height defined on the element for mobile devices
        $('#nav-wrap').removeAttr('style');
    }
}

/**
 * Updates links to other products and languages to contain the current member
 * if it is available.
 *
 * @param member - the member in question (dot-notation)
 */
function updateMemberLinks(member) {
    var $links = $('.update-page'),
        availableProducts = getMemberInfo(member).products || {},
        availableProduct;
    $links.each(function (i, link) {
        link.href = link.href.substring(0, link.href.lastIndexOf('/')) + '/';
        for (i = 0; i < availableProducts.length; i++) {
            availableProduct = availableProducts[i]
            if (link.id.indexOf(availableProduct) >= 0) {
                link.href += member;
                break;
            }
        }

    });
}

/**
 * Simulates a click on a link to a member by loading it with JS through gotoSection().
 * If an event is provided, its preventDefault() is called, and history is rewritten
 * with window.history.pushState().
 *
 * @param member - the id of a member, e.g. "exporting.chartOptions" (dot-notation)
 * @param e - the click event
 */
function memberClick(member, e) {
    var path = location.pathname,
        url;

    // Handle history only if there was an event.
    // If not, this function was called by accessing
    // the site or navigating the history.
    if (e !== undefined) {
        // Prevents the page to be loaded from the server
        e.preventDefault();

        // Remove trailing slash
        path = path.replace(/\/$/, '');

        if (page.length < 1) {
            // Add member to url if there was no existing page
            url = path + '/' + member;
        } else {
            // Remove old member from path and add new member if there was a page
            url = path.substring(0, path.lastIndexOf('/')) + '/' + member;
        }

        // Update page variable to member
        page = member.replace(/\//g, '');

        if (historyEnabled()) {
            window.history.pushState({'page': page}, member, url);
        } else {
            window.location.hash = member;
        }

    }

    // Load content
    gotoSection(member, true);

    // Lastly, update the height of the nav and wrapper
    updateHeight();
}

/**
 * Checks if a string has a value.
 * @param string - the string to check
 * @returns {boolean} true if the string is neither undefined or empty
 */
function strHasValue(string) {
    return string !== undefined && string.length > 0;
}

/**
 * Returns a the same string with capitalized first letter
 * E.g. "highcharts" returns "Highcharts"
 *
 * @param {string} string - the string to capitalize
 *
 * @returns {string} a string with capitalized first letter
 */
function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * Get the path between domain name and member
 * E.g. localhost:8080/highcharts-api/highcharts/data
 *                       |        base path        |
 *
 * @returns {string} the path between domain name and member
 */
function getBasePath() {
    var ctxt = CTXT.replace('/', ''),
        prod = PRODUCTNAME + '/';
    if (strHasValue(ctxt)) {
        ctxt += '/';
    }
    return ctxt + prod;
}

/**
 * Sets the first part of the document title to the member name, and returns it.
 * E.g. "exporting.buttons.contextButton" sets
 * "exporting.buttons.contextButton | Highcharts API Reference" as the document
 * title.
 *
 * @param {string} memberName
 *                      - name of the member, e.g.
 *                      "exporting.buttons.contextButton" (dot-notation)
 *
 * @returns {string} the page title
 */
function memberToDocumentTitle(memberName) {
    var title,
        prettyName = getMemberInfo(memberName).prettyName;

    title = prettyName + ' | ' + capitalizeFirstLetter(PRODUCTNAME) + ' API Reference';
    if (prettyName !== undefined) {
        document.title = title;
    }
    return title;
}

/**
 * Sets the page content to the splash page
 */
function showSplashPage() {
    var $splashPage = $('#splashText'),
        $plus = $('.plus');

    if ($section) {
        $section.hide();
    }

    if ($plus.hasClass('expanded')) {
        $plus.removeClass('expanded');
        $plus.addClass('collapsed');
        $plus.find('div[id$="-menu"]').slideUp();
    }

    $splashPage.show();
}

function loadOptionMemberInSection(obj, isParent) {
    //add member to section in div#details
    var $_section = $('div#' + obj.parent.replace('<', '\\<').replace('>', '\\>') + '.section'),
        $memberDiv,
        contextClass = obj.description && obj.description.indexOf('<p>') > -1 ? '' : ' context';

    $memberDiv = $('<div class="member" id="' + obj.name + '"><h2 class="title">' + obj.title + '</h2>'
        + (obj.returnType ? '<span class="returnType">: ' + markupReturnType(obj.returnType) + '</span>' : '')
        + (obj.deprecated ? '<div class="deprecated"><p>Deprecated</p></div>' : '' )
        + (obj.since ? '<div class="since">Since ' + obj.since + '</div>' : '' )
        + (obj.description ? '<div class="description">' + obj.description
            + (obj.defaults ? ' Defaults to <code>' + escapeHTML(obj.defaults) + '</code>.' : '')
            + '</div>' : '')
        + (obj.context ? '<div class="description' + contextClass + '">The <code>this</code> keyword refers to the ' + markupReturnType(obj.context) + ' object.</div>' : '')
        + (obj.demo ? '<div class="demo"><h4>Try it:</h4> ' + obj.demo + '</div>' : '' )
        + (obj.seeAlso ? '<div class="see-also"><h4>See also:</h4> ' + obj.seeAlso + '</div>' : '' )
        + '</div>').appendTo($_section);

    activateInternalLinks($memberDiv);

    $('div#' + escapeSelector(obj.name) + '.member h2.title').html(function () {
        var title = $.trim($(this).text());
        return $('<a href="/' + getBasePath() + obj.fullname + '" ' + (isParent ? '' : 'class="noChildren"') + '>' + title + '</a>').click(function (e) {
            memberClick(obj.fullname, e);
        });
    });
}

function loadObjectMemberInSection(obj) {
    $memberDiv = $('<div class="member" id="' + obj.name + '">'
        + '<h2 class="title">' + obj.title + '</h2> '
        + (obj.params ? '<span class="parameters">' + obj.params + '</span>' : '')
        + (obj.since ? '<div class="since">Since ' + obj.since + '</div>' : '' )
        + (obj.deprecated ? '<div class="deprecated"><p>Deprecated</p></div>' : '' )
        + '<div class="description"><p>' + obj.description + '</p>'
        + (obj.paramsDescription ? '<h4>Parameters</h4><ul id="paramdesc"><li>' +
            obj.paramsDescription.replace(/\|\|/g, '</li><li>') + '</li></ul>' : '')
        + (obj.returnType ? '<h4>Returns</h4><ul id="returns"><li>' + markupReturnType(obj.returnType) + '</li></ul>' : '')
        + '</div>'
        + (obj.demo ? '<div class="demo"><h4>Try it:</h4> ' + obj.demo + '</div>' : '' )
        + '</div>').appendTo('div#object-' + obj.parent + '.section');

    $('div#' + escapeSelector(obj.name) + '.member h2.title').html(function () {
        var title = $.trim($(this).text());
        return $('<a href="/' + getBasePath() + obj.fullname + '" class="noChildren">' + title + '</a>').click(function (e) {
            memberClick(obj.fullname, e);
        });
    });
    activateInternalLinks($memberDiv);
}

function loadChildren(name, silent, callback) {

    var isObject = /[A-Z]/.test(name[0]),
        url = CTXT + '/' + (isObject ?
                'object/' + PRODUCTNAME + '-obj/child/' + name :
                'option/' + PRODUCTNAME + '/child/' + name);

    // If url has been used to load children before, do not load them again
    if ($.inArray(url, usedUrls) !== -1) {
        return;
    }
    // Add the url to the list of used urls
    usedUrls.push(url);

    $.ajax({
        type: "GET",
        url: url,
        dataType: "json",
        error: function () {
            var $menu;
            $menu = $('div#' + escapeSelector(name) + '-menu');
            $('.dots', $menu.parent()).removeClass('loading').addClass('error').html('Error');
        },
        success: function (data) {
            var display = 'block',
                $menu, $menuItem;

            if (silent) {
                display = 'none';
            }

            name = name.replace('<', '\\<').replace('>', '\\>');
            $menu = $('div#' + name + '-menu');


            $.each(data, function (key, val) {
                var $div = $('<div></div>').appendTo($menu), $plus, $menuLink,
                    name,
                    title,
                    defaults,
                    cls;

                // Remove duplicate series<seriesType>.type-properties
                if (/series<.+>--type/.test(val.name)) {
                    return true; // return true in $.each() is the same as continue loop
                }

                // Make info available for e.g. rich cards
                storeMember(val);

                /*if (val.type === 'method') {
                 name = val.name.replace('--', '.') + '()';
                 } else if (val.type === 'property') {
                 name = val.name.replace('--', '.');
                 } else {
                 name = val.fullname;
                 }*/
                name = val.fullname;

                if (val.isParent) {
                    var preBracket = '{',
                        postBracket = '}';

                    if (val.returnType && val.returnType.indexOf('Array') === 0) {
                        preBracket = '[{';
                        postBracket = '}]';
                    }


                    $menuItem = $('<div class="menuitem collapsed"></div>');
                    $menuLink = $('<a href="/' + getBasePath() + name + '">' + val.title + '</a>').appendTo($menuItem);

                    $menuLink.click(function (e) {
                        memberClick(val.fullname, e);
                    });
                    $plus = $('<a href="/' + getBasePath() + name + '" class="plus"></a>').appendTo($menuItem);
                    $plus.click(function (e) {
                        e.preventDefault();
                        if ($plus.parent().hasClass('collapsed')) {
                            $menuLink.click();
                        } else {
                            toggleExpand($plus.parent());
                        }
                    });
                    $menuItem.append(':&nbsp;' + preBracket + '<span class="dots"><span>…</span></span>');
                    // add empty submenu
                    $('<div id="' + val.name + '-menu" style="display:none"><div>').appendTo($menuItem);
                    $menuItem.append(postBracket);
                    $menuItem.appendTo($menu);
                    addSectionOption(val);
                } else {
                    if (val.type === 'method') {
                        title = val.title + '()';
                        methods.push(val.fullname);
                    } else {
                        title = val.title;
                    }

                    $menuLink = $('<a href="/' + getBasePath() + name + '">' + title + '</a>').appendTo($div);
                    $menuLink.click(function (e) {
                        hideSidebar();
                        memberClick(name, e);
                    });
                    if (val.type === 'method') {
                        defaults = '[function]';
                    } else if (val.type === 'property') {
                        defaults = '[' + val.returnType + ']';
                    } else if (val.defaults === 'null' || val.defaults === 'undefined' || val.defaults === '' || val.defaults === undefined) {
                        defaults = val.defaults;
                    } else if (val.returnType === 'String' || val.returnType === 'Color') {
                        defaults = '"' + val.defaults + '"';

                    } else {
                        defaults = val.defaults;
                    }

                    if (val.returnType) {
                        cls = val.returnType.toLowerCase();
                    } else {
                        cls = '';
                        console.warn('Missing returnType for ' + val.fullname);
                    }


                    $('<span class="value value-' + cls + '">: ' + escapeHTML(defaults) + '</span>').appendTo($div);
                }
                if (isObject) {
                    loadObjectMemberInSection(val);
                } else {
                    loadOptionMemberInSection(val, val.isParent);
                }
            });

            $(document).triggerHandler({
                type: "xtra.btn.member.event",
                id: isObject ? 'object-' + name : name,
                table: isObject ? 'object' : 'option'
            });

            if (callback) {
                callback();
            }
        }
    });
}

function gotoSection(anchor, hilighted) {

    var name,
        levels,
        $_parentparent,
        callbackStack = [];

    // Handle typed parent item, like series<line>
    name = anchor.split('.');
    if (name.length > 1) {
        name[name.length - 1] = '-' + name[name.length - 1];
    }
    name = name.join('-');

    levels = name.split(/[-]{1,2}/);

    // Asyncronously expand parent elements of selected item
    $.each(levels, function (i) {
        callbackStack.push(function () {
            var proceed = true,
                level,
                $_menu,
                $_parent;

            if (levels[i]) {
                level = levels.slice(0, i + 1).join('-');

                if (level.indexOf('<') > -1) {
                    $_parentparent = $('#' + level.split('<')[0] + '-menu').parent();
                    level = escapeSelector(level);
                }

                $_menu = $('#' + level + '-menu');
                $_parent = $_menu.parent();

                if ($_menu && $_parent.hasClass('collapsed')) {

                    if ($_parentparent && $_parentparent.hasClass('collapsed')) {
                        toggleExpand($_parentparent);
                    }
                    // Do the toggle, and pass the next level as the callback argument
                    toggleExpand($_parent, callbackStack[i + 1]);
                    proceed = false;
                }
            }

            if (level) {
                // For the last path item, show the section etc
                if (/[A-Z]/.test(level[0])) {
                    level = 'object-' + level;
                }
                if ($('#details > div.section#' + level).length) {
                    toggleSection(level);

                    // empty search
                    $("#search").val("");

                }
            }

            if (proceed && callbackStack[i + 1]) {
                callbackStack[i + 1]();
            }
        });
    });

    // Hilighting is the last operation in the async stack
    if (hilighted) {
        callbackStack.push(function () {
            if (strHasValue(name)) {
                // Highlight if there was a member
                // E.g. product#some.member
                hilight(name);
                // Update the Google Rich Card
                modifyRichCard(anchor);
                // Set the page title
                memberToDocumentTitle(anchor);
                // Update the links with class 'update-page' to contain the member path
                updateMemberLinks(anchor);
            } else {
                showSplashPage();
            }
        });
    }

    // Start the recursive iteration
    callbackStack[0]();
}

/**
 * Add the first level menu items on page load
 */
function addFirstLevelMenuItem(key, val, type) {


    var $menuItem = $('<div class="menuitem collapsed"></div>').appendTo('#' + type + 's'),
        $plus, $menuLink,
        sectionId = val.fullname || val.name,
        title = escapeHTML(val.title),
        mainSection,
        name = val.name,
        recurseToType = false,
        menuItemPrefix = '',
        prefix = ': {',
        suffix = '}';

    // Make info available for e.g. rich cards
    storeMember(val);

    if (val.returnType && val.returnType.indexOf('Array') === 0) {
        if (val.returnType === 'Array<Object>') {
            prefix = ': [{';
            suffix = '}]';
        } else {
            prefix = ': [';
            suffix = ']';
        }
    }

    // Global options
    if ($.inArray(val.name, ['global', 'lang']) !== -1) {
        $menuItem = $('<div class="menuitem collapsed"></div>').appendTo('#global-options');
    }


    // Handle the series<line> syntax
    if (sectionId.indexOf('<') > -1) {
        mainSection = sectionId.split('<')[0];

        // The first time we encounter a menu item on the syntax series<line>, add the series menu item
        if ($('#' + mainSection + '-menu').length === 0) {
            sectionId = title = name = mainSection;
            prefix = ': [';
            suffix = ']';
            recurseToType = true; // run this method again, but now for the { type: "line" } menu item
        } else {
            $menuItem.appendTo($('#' + mainSection + '-menu'));
            menuItemPrefix = '{<br class="typed"/>';
            title = '<span class="typed">type: "' + sectionId.split('<')[1].split('>')[0] + '"</span>';
            prefix = ', ';
        }


    }

    if (menuItemPrefix) {
        $menuItem.append(menuItemPrefix);
    }

    $menuLink = $('<a href="/' + getBasePath() + sectionId + '">' + title + '</a>')
        .appendTo($menuItem)
        .click(function (e) {
            memberClick(sectionId, e);
            return false;
        });

    if (val.isParent) {
        $plus = $('<a href="/' + getBasePath() + sectionId + '" class="plus"></a>')
            .appendTo($menuItem)
            .click(function (e) {
                e.preventDefault();
                if ($plus.parent().hasClass('collapsed')) {
                    $menuLink.click();
                } else {
                    toggleExpand($plus.parent());
                }
            });
    }

    $menuItem.append(prefix);

    $('<span class="dots"><span>…</span></span>').appendTo($menuItem);

    if (val.isParent) {
        $('<div id="' + name + '-menu" style="display:none"><div>').appendTo($menuItem);
    }

    $menuItem.append(suffix);


    // create sections in div#details
    if (type === 'option') {
        addSectionOption(val);
    } else {
        addSectionObject(val);
    }

    if (recurseToType) {
        addFirstLevelMenuItem.apply(null, arguments);
    }
}

prepareOffline = function (callback) {

    offline = {highcharts: {}, highstock: {}, highmaps: {}};

    // now we have the data loaded we rewrite $.ajax for offline use
    $.ajax = function (obj) {
        var result,
            splitted;

        if (obj.url === '/' + PRODUCTNAME + '/names') {
            result = API[PRODUCTNAME].names;
        }

        if (obj.url === '/option/' + PRODUCTNAME + '/main') {
            result = API[PRODUCTNAME].main.option;
        }

        if (obj.url === '/object/' + PRODUCTNAME + '-obj/main') {
            result = API[PRODUCTNAME].main.object;
        }

        splitted = obj.url.split('object/' + PRODUCTNAME + '-obj/child/');
        if (splitted.length > 1) {
            result = API[PRODUCTNAME].object[splitted[1]].children;
        }
        splitted = obj.url.split('option/' + PRODUCTNAME + '/child/');
        if (splitted.length > 1) {
            result = API[PRODUCTNAME].option[splitted[1]].children;
        }

        // result to handler
        obj.success(result);
    };

    callback();
};

// build dictionary for offline use
buildApiOffline = function (data, callback) {

    var option,
        names,
        type,
        i = 0;

    API[PRODUCTNAME] = {option: [], object: [], main: {}, names: []};

    names = API[PRODUCTNAME].names;

    function fillWithType(type) {
        var idx,
            slot = API[PRODUCTNAME][type],
            main = API[PRODUCTNAME].main[type] = [],
            name;

        // Loop over options in dump file
        for (idx = 0; idx < data[type].length; idx++) {
            option = data[type][idx];
            name = option.name;
            names.push(name);

            if (option.isParent) {

                // Store main options separately
                if (!/-/.test(name)) {
                    main.push(option);
                }

                if (slot[name] == undefined) {
                    slot[name] = {details: option, children: []};
                } else {
                    /* In case the parent option was already
                     * deducted from a child option
                     */
                    slot[name].details = option;
                }
            }

            // we have a child!
            if (slot.hasOwnProperty(option.parent)) {
                slot[option.parent].children.push(option);
            } else {
                slot[option.parent] = {details: null, children: [option]};
            }
        }
    }

    while (i < 2) {
        type = ['option', 'object'][i];
        fillWithType(type);
        i++
    }

    callback();

};

buildPage = function () {

    // autocomplete
    $.ajax({
        type: "GET",
        url: CTXT + '/' + PRODUCTNAME + '/names',
        // Always load synchronously
        async: false,
        dataType: "json",
        success: function (data) {
            $.each(data, function (key, val) {

                if (strHasValue(val)) {
                    var dotted = toDot(val);

                    names.push(dotted);
                    optionDictionary[dotted] = val;
                }
            });

            $("#search").autocomplete({
                source: names,
                autoFocus: true,
                minLength: 2,
                select: function (event, ui) {
                    memberClick(ui.item.value, event);
                },
                position: {
                    my: 'left top',
                    of: '#search-wrap'
                }
            });
        }
    });

    // load main options and build folded menu tree
    $.ajax({
        type: "GET",
        url: CTXT + '/option/' + PRODUCTNAME + '/main',
        // Always load synchronously
        async: false,
        dataType: "json",
        success: function (data) {
            var globals = false;
            $.each(data, function (key, val) {
                addFirstLevelMenuItem(key, val, 'option');
                if ($.inArray(val.name, ['global', 'lang']) !== -1) {
                    globals = true;
                }
            });
            if (!globals) {
                $('#global-options-tree').hide();
            }
        }
    });

    // load objects of product
    $.ajax({
        type: "GET",
        url: CTXT + '/object/' + PRODUCTNAME + '-obj/main',
        // Always load synchronously
        async: false,
        dataType: "json",
        success: function (data) {
            $.each(data, function (key, val) {
                addFirstLevelMenuItem(key, val, 'object');
            });
            if (data.length < 1) {
                $('#objects-nav-section').hide();
            }
        },
        /**
         * Hides the Objects nav section if there were no objects found for the product
         * @param jqXHR
         * @param textStatus
         * @param errorThrown
         */
        error: function (jqXHR, textStatus, errorThrown) {
            console.error('Failed to retrieve objects for ' + PRODUCTNAME + '.', jqXHR, textStatus, errorThrown);
            $('#objects-nav-section').hide();
        }
    });

    // check url for anchor, remove also '()' from old links for object.method().
    anchor = window.location.hash.replace('#', '').replace('()', '');
    if (strHasValue(anchor)) {
        memberClick(anchor);
    }

    if (/\?object_not_found=true/.test(window.location.search)) {
        dottedName = window.location.hash.split('#').pop();
        internalName = optionDictionary[dottedName];
        $('div#' + internalName).append('<div class="error">The object/option wasn\'t found in the database, maybe iẗ́\'s inherited??</div>');
    }

    // focus search
    $("#search")[0].focus();
};

/**
 * Checks if the sidebar is open based on the body class.
 *
 * @returns {boolean} true if the sidebar is open; false if not
 */
function sidebarIsOpen() {
    return $('body').hasClass('sidr-open');
}

/**
 * Hides the sidebar if it is open.
 */
function hideSidebar() {
    if (sidebarIsOpen()) {
        $('#sidebar-nav-link').click();
    }
}

/**
 * Initializes the sidebar functionality.
 */
function initializeSidebar() {
    // Sidr sidebar activation
    $('.sidebar-nav-link').sidr({
        name: 'nav',
        displace: false
    });

    // Make clicking the page wrapper and nav links also collapse the sidebar
    $('#details-wrap').on('click', function () {
        hideSidebar();
    });
}

/**
 * Initializes a dropdown with a given name prefix,
 * by setting the 'expanded' attribute on the dropdown link and list.
 *
 * The dropdown structure needs to contain a link and a list with
 * the same name prefix. Example:
 *
 *     <a id="[name]-link" expanded="false"></a>
 *     <ul id="[name]-list" expanded="false>
 *         ...
 *     </ul>
 *
 * @param name - the name of the dropdown
 */
function initializeDropdown(name) {
    var $list = $('#' + name + '-list'),
        $link = $('#' + name + '-link');
    $link.on('click', function (e) {
        e.preventDefault();
        if ($link.attr('expanded') === 'true') {
            $link.attr('expanded', false);
            $list.attr('expanded', false);
        } else {
            $link.attr('expanded', true);
            $list.attr('expanded', true);
        }
    });

    $('#details-wrap').on('click', function () {
        $link.attr('expanded', false);
        $list.attr('expanded', false);
    });
}

/**
 * Adds simulation of history navigation by detecting changes to the history state.
 *
 * @return [undefined] - nothing
 */
function simulateHistory() {

    if (historyEnabled()) { // Use the history API if available
        /**
         * Updates the history with memberClick().
         *
         * If it is stored in the history state, the page will be used to update.
         * If not, the global PAGE variable will be used.
         *
         * @param e - the event that triggered the history update
         */
        window.onpopstate = function (e) {
            console.log('@updateHistory', PAGE, e);
            if (e.state !== undefined && e.state !== null && e.state.page !== undefined) {
                memberClick(e.state.page);
            } else {
                memberClick(PAGE);
            }
        }
    } else { // Use the #-notation if history API is not available
        window.onhashchange = function (e) {
            memberClick(window.location.hash.replace(/#/, ''));
        }
    }
}

// Startup
$(function () {
    var hash = location.hash,
        href,
        url;

    // Fallback for old urls with # instead of /.
    // Replaces # with /
    if (strHasValue(hash)) {
        page = hash.replace(/#/, '');
        href = hash.replace(/#/, '/');
        url = location.pathname + href;
        if (historyEnabled()) {
            window.history.replaceState({'page': page}, href, url);
        } else {
            PAGE = page;
        }
    }

    // Initialize sidr sidebar
    initializeSidebar();

    // Initialize the programming language selector
    initializeDropdown('products');
    initializeDropdown('prog-lang-selector');

    if (runDB) {
        buildPage();
    } else {
        // prepare dump object
        prepareOffline(function () {
            // load offline data
            loadScript('./js/' + PRODUCTNAME + '.json', function () {
                buildApiOffline(offline[PRODUCTNAME], buildPage);
            });
        });
        // hide elements that don't make sence in offline mode
        $('.hidden-offline').hide();
    }

    // convert hash from redirected dash syntax to new dot syntax
    if (/-/.test(location.hash)) {
        location.hash = location.hash.replace(/(--|-)/g, '.');
    }

    // Add scrollanimation to button
    $("a[href='#top']").click(function () {
        $("html, body").animate({scrollTop: 0}, "slow");
        return false;
    });

    $(window).on('scroll', function () {
        var button = $("#scrollTop");
        if (!$("#top").isOnScreen()) {
            if (button.css('display') == 'none') {
                button.fadeIn("slow");
            }
        } else {
            if (button.css('display') == 'block') {
                button.fadeOut("slow");
            }
        }
    });

    $.fn.isOnScreen = function () {
        var win = $(window),
            viewport = {
                top: win.scrollTop(),
                left: win.scrollLeft()
            };

        viewport.right = viewport.left + win.width();
        viewport.bottom = viewport.top + win.height();

        var bounds = this.offset();
        bounds.right = bounds.left + this.outerWidth();
        bounds.bottom = bounds.top + this.outerHeight();

        return (!(viewport.right < bounds.left || viewport.left > bounds.right || viewport.bottom < bounds.top || viewport.top > bounds.bottom));

    };

    updateHeight();

    $(window).resize(updateHeight);

    // Make the Highcharts/Highstock links dynamic
    $('#highstock-link, #highcharts-link').click(function () {
        this.href += location.hash;
    });

    // Login shortcut (hot corner)
    $("<div>")
        .css({
            position: 'absolute',
            display: 'block',
            width: '10px',
            height: '10px',
            right: 0,
            cursor: 'pointer'
        })
        .click(function () {
            var ctxt = strHasValue(CTXT) ? CTXT.replace(/\//g, '') + '/' : '';

            $('<iframe src="/' + ctxt + 'auth/login">').dialog({
                height: 300
            });
        })
        .prependTo('#top .container');

    // Call the custom simulateHistory() function to allow history navigation
    // with 'back' and 'forward'
    simulateHistory();

    if (strHasValue(page)) {
        memberClick(page);
    }

});
