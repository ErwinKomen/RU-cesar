var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

var ru = (function ($, ru) {
  "use strict";

  ru.cesar.seeker = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        loc_divErr = "research_err",
        loc_bExeErr = false,          // Internal way to see that an execution error has occurred
        oSyncTimer = null,
        loc_sWaiting = " <span class=\"glyphicon glyphicon-refresh glyphicon-refresh-animate\"></span>",
        loc_towards = [],             // Copy of the most updated TOWARDS table
        loc_related = [],             // Which related variable has which towards choice
        loc_bRelated = true,          // Flag that related is okay
        loc_sRelatedErr = "",         // Related error
        basket_progress = "",         // URL to get progress
        basket_start = "",            // URL to start Translation + Execution
        basket_stop = "",             // URL to stop the basket
        basket_watch = "",            // URL to watch basket that is in progress
        basket_result = "",           // URL to the results for this basket
        loc_bSimpleNameError = false,
        basket_data = null,           // DATA to be sent along
        lAddTableRow = [
          { "table": "research_intro-wrd", "prefix": "wrdconstruction", "counter": true, "events": null},
          { "table": "research_intro-cns", "prefix": "cnsconstruction", "counter": true, "events": null },
          { "table": "research_shareg", "prefix": "shareg", "counter": false, "events": null },
          { "table": "research_gvar", "prefix": "gvar", "counter": false, "events": null },
          { "table": "research_vardef", "prefix": "vardef", "counter": false, "events": null },
          { "table": "research_spec", "prefix": "function", "counter": false, "events": null },
          { "table": "research_cond", "prefix": "cond", "counter": true, "events": function () { ru.cesar.seeker.init_cond_events(); } },
          { "table": "research_feat", "prefix": "feat", "counter": true, "events": function () { ru.cesar.seeker.init_feat_events(); } },
          { "table": "result_kwicfilter", "prefix": "filter", "counter": true, "events": null },
          {"table": "search_mode_simple", "prefix": "simplerel", "counter": true,
          "events": function () { ru.cesar.seeker.init_simple_events(); }, "follow": function () { ru.cesar.seeker.simple_update(); }
          }
      ];


    // Private methods specification
    var private_methods = {
      /**
       * fitFeatureBox
       *    Initialize the <svg> in the @sDiv
       * 
       * @param {object} oBound
       * @param {el} elTarget
       * @returns {object}
       */
      fitFeatureBox: function (oBound, elTarget) {
        var rect = null;

        try {
          // Take into account scrolling
          oBound['x'] -= document.documentElement.scrollLeft || document.body.scrollLeft;
          oBound['y'] -= document.documentElement.scrollTop || document.body.scrollTop;
          // Make sure it all fits
          if (oBound['x'] + $(elTarget).width() + oBound['width'] + 10 > $(window).width()) {
            oBound['x'] -= $(elTarget).width() + oBound['width'];
          } else if (oBound['x'] < 0) {
            oBound['x'] = 10;
          }
          if (oBound['y'] + $(elTarget).height() + oBound['height'] + 10 > $(window).height()) {
            oBound['y'] -= $(elTarget).height() + oBound['height'];
          } else if (oBound['y'] < 0) {
            oBound['y'] = 10;
          } else {
            oBound['y'] += oBound['height'] + 10;
          }
          // Take into account scrolling
          oBound['x'] += document.documentElement.scrollLeft || document.body.scrollLeft;
          oBound['y'] += document.documentElement.scrollTop || document.body.scrollTop;
          return oBound;
        } catch (ex) {
          private_methods.showError("fitFeatureBox", ex);
          return oBound;
        }
      },
      /**
       * methodNotVisibleFromOutside - example of a private method
       * @returns {String}
       */
      methodNotVisibleFromOutside: function () {
        return "something";
      },

      /**
       *  is_in_list
       *      whether item called sName is in list lstThis
       *
       * @param {list} lstThis
       * @param {string} sName
       * @returns {boolean}
       */
      is_in_list: function (lstThis, sName) {
        var i = 0;

        try {
          for (i = 0; i < lstThis.length; i++) {
            if (lstThis[i]['name'] === sName) {
              return true;
            }
          }
          // Failure
          return false;
        } catch (ex) {
          private_methods.showError("is_in_list", ex);
          return false;
        }
      },

      /**
       *  get_list_value
       *      get the value of the item called sName is in list lstThis
       *
       * @param {list} lstThis
       * @param {string} sName
       * @returns {string}
       */
      get_list_value: function (lstThis, sName) {
        var i = 0;

        try {
          for (i = 0; i < lstThis.length; i++) {
            if (lstThis[i]['name'] === sName) {
              return lstThis[i]['value'];
            }
          }
          // Failure
          return "";
        } catch (ex) {
          private_methods.showError("get_list_value", ex);
          return "";
        }
      },

      /**
       *  set_list_value
       *      Set the value of the item called sName is in list lstThis
       *
       * @param {list} lstThis
       * @param {string} sName
       * @param {string} sValue
       * @returns {boolean}
       */
      set_list_value: function (lstThis, sName, sValue) {
        var i = 0;

        try {
          for (i = 0; i < lstThis.length; i++) {
            if (lstThis[i]['name'] === sName) {
              lstThis[i]['value'] = sValue;
              return true;
            }
          }
          // Failure
          return false;
        } catch (ex) {
          private_methods.showError("set_list_value", ex);
          return false;
        }
      },

      /**
       * prepend_styles
       *    Get the html in sDiv, but prepend styles that are used in it
       * 
       * @param {el} HTML dom element
       * @returns {string}
       */
      prepend_styles: function (sDiv, sType) {
        var lData = [],
            el = null,
            i, j,
            sheets = document.styleSheets,
            used = "",
            elems = null,
            tData = [],
            rules = null,
            rule = null,
            s = null,
            sSvg = "",
            defs = null;

        try {
          // Get the correct element
          if (sType === "svg") { sSvg = " svg";}
          el = $(sDiv + sSvg).first().get(0);
          // Get all the styles used 
          for (i = 0; i < sheets.length; i++) {
            rules = sheets[i].cssRules;
            for (j = 0; j < rules.length; j++) {
              rule = rules[j];
              if (typeof (rule.style) !== "undefined") {
                elems = el.querySelectorAll(rule.selectorText);
                if (elems.length > 0) {
                  used += rule.selectorText + " { " + rule.style.cssText + " }\n";
                }
              }
            }
          }

          // Get the styles
          s = document.createElement('style');
          s.setAttribute('type', 'text/css');
          switch (sType) {
            case "html":
              s.innerHTML = used;

              // Get the table
              tData.push("<table class=\"func-view\">");
              tData.push($(el).find("thead").first().get(0).outerHTML);
              tData.push("<tbody>");
              $(el).find("tr").each(function (idx) {
                if (idx > 0 && !$(this).hasClass("hidden")) {
                  tData.push(this.outerHTML);
                }
              });
              tData.push("</tbody></table>");

              // Turn into a good HTML
              lData.push("<html><head>");
              lData.push(s.outerHTML);
              lData.push("</head><body>");
              // lData.push(el.outerHTML);
              lData.push(tData.join("\n"));
              
              lData.push("</body></html>");
              break;
            case "svg":
              s.innerHTML = "<![CDATA[\n" + used + "\n]]>";

              defs = document.createElement('defs');
              defs.appendChild(s);
              el.insertBefore(defs, el.firstChild);

              el.setAttribute("version", "1.1");
              el.setAttribute("xmlns", "http://www.w3.org/2000/svg");
              el.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");
              lData.push("<?xml version=\"1.0\" standalone=\"no\"?>");
              lData.push("<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\" \"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\" >");
              lData.push(el.outerHTML);
              break;
          }

          return lData.join("\n");
        } catch (ex) {
          private_methods.showError("prepend_styles", ex);
          return "";
        }
      },

      /**
       * screenCoordsForRect
       *    Get the correct screen coordinates for the indicated <svg> <rect> element
       * 
       * @param {el} svgRect
       * @returns {object}
       */
      screenCoordsForRect: function (svgRect) {
        var pt = null,
            elSvg = null,
            rect = null,
            oBound = {},
            matrix;

        try {
          // Get the root <svg>
          elSvg = $(svgRect).closest("svg").get(0);

          rect = svgRect.get(0);
          oBound = rect.getBoundingClientRect();

          // Take into account scrolling
          oBound['x'] += document.documentElement.scrollLeft || document.body.scrollLeft;
          oBound['y'] += document.documentElement.scrollTop || document.body.scrollTop;
          return oBound;
        } catch (ex) {
          private_methods.showError("screenCoordsForRect", ex);
          return oBound;
        }

      },
      /**
       *  var_move
       *      Move variable row one step down or up
       *      This means the 'order' attribute changes
       */
      var_move: function (elStart, sDirection, sType) {
        var elRow = null,
            el = null,
            tdCounter = null,
            rowSet = null,
            iLen = 0;

        try {
          // Find out what type we have
          if (sType === undefined) { sType = ""; }
          switch (sType) {
            case "selected":
              // Find the selected row
              elRow = $(elStart).closest("form").find("tr.selected").first();
              // The element is below
              el = $(elRow).find(".var-order input").parent();
              break;
            default:
              // THe [el] is where we start
              el = elStart;
              // The row is above me
              elRow = $(el).closest("tr");
              break;
          }
          // Perform the action immediately
          switch (sDirection) {
            case "down":
              // Put the 'other' (=next) row before me
              $(elRow).next().after($(elRow));
              break;
            case "up":
              // Put the 'other' (=next) row before me
              $(elRow).prev().before($(elRow));
              break;
            default:
              return;
          }
          // Now iterate over all rows in this table
          rowSet = $(elRow).parent().children(".form-row").not(".empty-form");
          iLen = $(rowSet).length;
          $(rowSet).each(function (index, el) {
            var elInput = $(el).find(".var-order input");
            var sOrder = $(elInput).val();
            // Set the order of this element
            if (parseInt(sOrder, 10) !== index + 1) {
              $(elInput).attr("value", index + 1);
              $(elInput).val(index + 1);
              // Look for a <td> element with class "counter"
              tdCounter = $(el).find("td.counter");
              if (tdCounter.length > 0) {
                $(tdCounter).html(index+1);
              }
            }
            if (sType === "") {
              // Check visibility of up and down
              $(el).find(".var-down").removeClass("hidden");
              $(el).find(".var-up").removeClass("hidden");
              if (index === 0) {
                $(el).find(".var-up").addClass("hidden");
              }
              if (index === iLen - 1) {
                $(el).find(".var-down").addClass("hidden");
              }
            }
          });
        } catch (ex) {
          private_methods.errMsg("var_move", ex);
        }
      },
      errMsg: function (sMsg, ex, bNoCode) {
        var sHtml = "",
            bCode = true;

        // Check for nocode
        if (bNoCode !== undefined) {
          bCode = not(bNoCode);
        }
        // Replace newlines by breaks
        sMsg = sMsg.replace(/\n/g, "\n<br>");
        if (ex === undefined) {
          sHtml = "Error: " + sMsg;
        } else {
          sHtml = "Error in [" + sMsg + "]<br>" + ex.message;
        }
        sHtml = "<code>" + sHtml + "</code>";
        console.log(sHtml);
        $("#" + loc_divErr).html(sHtml);
      },
      errClear: function () {
        $("#" + loc_divErr).html("");
        loc_bExeErr = false;
      },
      mainWaitStart : function() {
        var elWait = $(".main-wait").first();
        if (elWait !== undefined && elWait !== null) {
          $(elWait).removeClass("hidden");
        }
      },
      mainWaitStop: function () {
        var elWait = $(".main-wait").first();
        if (elWait !== undefined && elWait !== null) {
          $(elWait).addClass("hidden");
        }
      },
      waitInit: function (el) {
        var elResPart = null,
            elWait = null;

        try {
          // Set waiting div
          elResPart = $(el).closest(".research_part");
          if (elResPart !== null) {
            elWait = $(elResPart).find(".research-fetch").first();
          }
          return elWait;
        } catch (ex) {
          private_methods.errMsg("waitInit", ex);
        }
      },
      waitStart: function(el) {
        if (el !== null) {
          $(el).removeClass("hidden");
        }
      },
      waitStop: function (el) {
        if (el !== null) {
          $(el).addClass("hidden");
        }
      }
    }

    // Public methods
    return {
      /**
       * argrow_click
       *   Show or hide the following <tr> element
       *   Also: adapt the +/- sign(s)
       */
      argrow_click: function (el, sClass, bShow) {
        var trNext = null;

        try {
          // Validate
          if (el === undefined) { return; }
          // Get the following <tr>
          trNext = $(el).closest("tr").next().first();
          if (trNext !== null) {
            // Check its current status
            if ($(trNext).hasClass("hidden") || (bShow !== undefined && bShow)) {
              // Show it
              $(trNext).removeClass("hidden");
              // Change the '+' into a '-'
              $(el).html("-");
            } else {
              // Hide it
              $(trNext).addClass("hidden");
              // Change the '-' into a '+'
              $(el).html("+");
              // Hide all underlying ones with class [sClass]
              if (sClass !== undefined && sClass !== "") {
                $(trNext).find("." + sClass).addClass("hidden");
                $(trNext).find(".arg-plus").html("+");
              }
            }
          }

        } catch (ex) {
          private_methods.errMsg("argrow_click", ex);
        }
      },
      /**
       * funchead_click
       *   Assuming we are on an element of class [func-plus]
       *     - close or open everything with style [sClass] below us
       *     - this depends on the 'sign' we have: + or -
       *   Also: adapt the +/- sign(s)
       */
      funchead_click: function (el, sClass) {
        var trNext = null,
            elTbody = null, // My own <tbody>
            sStatus = "";   // My own status

        try {
          // Validate
          if (el === undefined) { return; }
          // Get my status
          sStatus = $(el).text();   // This can be + or -
          // Get my own <tbody>
          elTbody = $(el).closest("table").children("tbody").first();
          // Check status
          if (sStatus == "-") {
            // We are open and need to close all below
            $(el).html("+");
            $(el).attr("title", "open");
            // Close all [arg-plus] below us
            $(elTbody).find(".arg-plus").html("+");
            $(elTbody).find(".func-plus").html("+");
            $(elTbody).find(".func-plus").attr("title", "open");
            $(elTbody).find(".func-inline").addClass("hidden");
          } else {
            // We are + (=closed) and need to open (become -)
            $(el).html("-");
            $(el).attr("title", "close");
            // Open all [arg-plus] below us
            $(elTbody).find(".arg-plus").html("-");
            $(elTbody).find(".func-plus").html("-");
            $(elTbody).find(".func-plus").attr("title", "close");
            $(elTbody).find(".func-inline").removeClass("hidden");
          }

        } catch (ex) {
          private_methods.errMsg("funchead_click", ex);
        }
      },
      /**
       * argtype_click
       *   Set the type of argument: fixed value, select or  calculate
       *
       *   Assumptions:
       *    0 = fixed value
       *    1 = global variable
       *    2 = construction variable
       *    3 = expression (function)
       *
       */
      argtype_click: function (el) {
        try {
          var elRow = (el.target === undefined) ? el : $(this).closest("tr");
          var elType = $(elRow).find(".arg-type").first();
          var elVal = $(elRow).find(".arg-val-exp").first();
          // Find the type element
          var elArgType = $(elType).find("select").first();
          // Get its value
          var elArgTypeVal = $(elArgType).val();
          // Hide/show, depending on the value
          $(elVal).find(".arg-value").addClass("hidden");
          $(elVal).find(".arg-expression").addClass("hidden");
          $(elVal).find(".arg-gvar").addClass("hidden");
          $(elVal).find(".arg-cvar").addClass("hidden");
          $(elVal).find(".arg-dvar").addClass("hidden");
          $(elVal).find(".arg-rcnst").addClass("hidden");
          $(elVal).find(".arg-raxis").addClass("hidden");
          $(elVal).find(".arg-rcond").addClass("hidden");
          $(elVal).find(".arg-search").addClass("hidden");
          switch (elArgTypeVal) {
            case "fixed": // Fixed value
              $(elVal).find(".arg-value").removeClass("hidden");
              break;
            case "gvar": // Global variable
              $(elVal).find(".arg-gvar").removeClass("hidden");
              break;
            case "cvar": // Constructuion variable
              $(elVal).find(".arg-cvar").removeClass("hidden");
              break;
            case "dvar": // Data-dependant variable
              $(elVal).find(".arg-dvar").removeClass("hidden");
              break;
            case "func": // Expression
              $(elVal).find(".arg-expression").removeClass("hidden");
              break;
            case "cnst":  // Constituent
              $(elVal).find(".arg-cnst").removeClass("hidden");
              break;
            case "raxis":  // Relation - axis
              $(elVal).find(".arg-raxis").removeClass("hidden");
              break;
            case "rcond":  // Relation - condition
              $(elVal).find(".arg-rcond").removeClass("hidden");
              break;
            case "rcnst":  // Relation - constituent
              $(elVal).find(".arg-rcnst").removeClass("hidden");
              break;
            case "hit":  // Search hit
              $(elVal).find(".arg-search").removeClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("argtype_click", ex);
        }
      },

      /**
       * ajaxcall
       *   Make an AJAX call to the URL with the data
       *   Use the method specified: POST or GET
       *
       */
      ajaxcall: function (sUrl, data, sMethod) {
        var response = {};

        try {
          // Initialisations
          response['status'] = "initializing";
          // Validate
          if (sUrl === undefined || sUrl === "" || data === undefined) {
            // Cannot do anything with this, so respond with a bad status
            response['status'] = "error";
            response['msg'] = "Missing obligatory parameter(s): URL, data";
            return response;
          }
          // There is valid information, continue
          $.ajax({
            url: sUrl,
            type: sMethod,
            data: data,
            async: false,
            dataType: 'json',
            success: function (data) {
              response = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
              var sMsg = "The ajaxcall [" + textStatus + "] returns an error response: " + jqXHR.responseText;
              private_methods.errMsg(sMsg);
            }
          });
          // Return the response
          return response;
        } catch (ex) {
          private_methods.errMsg("ajaxcall", ex);
        }
      },

      /**
       * ajaxform_click
       *   General way to process an ajax form request:
       *   1 - Issue a POST request to send (and save) data
       *   2 - Issue a GET request to receive updated data
       *
       */
      ajaxform_click: function () {
        var data = [],      // Array to store the POST data
            extra = [],     // Additional data
            elErr = null,   // The 'research_err' component under the <form>
            i,
            elCall = this,
            response = null,
            elWait = null,
            action = "",
            openurl = "",
            callType = "";  // Type of element that calls us

        try {
          // Set waiting div
          elWait = private_methods.waitInit(this);
          // Start waiting
          private_methods.waitStart(elWait);
          // /WHo is calling?
          callType = $(this)[0].tagName.toLowerCase();

          // obligatory parameter: ajaxurl
          var ajaxurl = $(this).attr("ajaxurl");
          var instanceid = $(this).attr("instanceid");
          openurl = $(this).attr("openurl");
          var elStart = $(this);
          var bNew = (instanceid.toString() === "None");
          action = $(this).attr("action");

          // Derive the data
          if ($(this).attr("data")) {
            data = $(this).attr("data");
          } else {
            var frm = $(this).closest("form");
            if (frm !== undefined) {
              data = $(frm).serializeArray();
              // Check if there is additional data
              if ($(this).attr("extra")) {
                extra = JSON.parse($(this).attr("extra"));
                for (i = 0; i < extra.length; i++) {
                  data.push(extra[i]);
                }
              }
            }
          }
          data.push({ 'name': 'instanceid', 'value': instanceid });
          // THird parameter: the id of the element to be opened: OPTIONAL
          var openid = $(this).attr("openid");
          // Find the element to be opened/closed
          var elOpen = null;
          if (openid !== undefined) {
            elOpen = $(this).closest("#" + openid);
          }

          // Indicate we are saving/preparing
          if (!bNew) {
            $(".save-warning").html("Saving item... " + instanceid.toString());
          }
          // Make an AJAX call to get an existing or new specification element HTML code
          response = ru.cesar.seeker.ajaxcall(ajaxurl, data, "POST");
          if (response.status === undefined || response.status !== 'ok') {
            // Show an error somewhere

          } else if (bNew && 'instanceid' in response) {
            // A new item has been created, and now we receive its 'instanceid'
            instanceid = response['instanceid'];
            // Add the instanceid to the URL, so that the new item gets opened
            ajaxurl = ajaxurl + instanceid + "/";
            // Also find the 'goto_overview' and adpat its @targeturl property
            var elOview = $("#goto_overview").children("button").first();
            if (elOview !== undefined && elOview !== null) {
              var sOviewUrl = $(elOview).attr("targeturl");
              sOviewUrl = sOviewUrl.replace("/new/", "/" + instanceid + "/");
              $(elOview).attr("targeturl", sOviewUrl);
              // Set a tag to indicate that we need to jump to a new item when returning
              $(elOview).attr("isnew", true);
            }
          }
          // Check whether we need to show the error response
          if ('has_errors' in response && response.has_errors) {
            // See if there is a 'research_err' component under the <form>
            elErr = $(this).closest("form").find("#research_err").first();
            // Do we have an 'err_view' html contents?
            if ('err_view' in response && elErr !== null) {
              $(elErr).html(response.err_view);
            } else if (response.html !== "") {
              // Yes, show the resulting form with the errors
              $(elOpen).html(response.html);
            } else {
              // There is an error, but it is not inside the HTML part
              if ('error_list' in response) {
                if (elErr !== null) {
                  $(elErr).html(response['error_list'].join("<br>"));
                }
              } else if (elErr !== null) {
                $(elErr).html("There is an error, but the nature of this error is not clear.");
              } else {
                private_methods.errMsg("There is an error, but the nature of this error is not clear.");
              }
            }
            // Make sure events are set again
            ru.cesar.seeker.init_events();
            // Bind the click event to all class="ajaxform" elements
            $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);
            // Stop waiting
            private_methods.waitStop(elWait);
            // Show that errors need to be repaired
            $(".save-warning").html("(not saved; there are errors)");
            // And return
            return;
          }

          // Continuation depends on the action
          switch (action) {
            case "save_function":
              // Show we are showing the function summary
              $('.save-warning').html("Updating the summary...");
              // Showing the summary
              var funcsum = $(elStart).closest(".func_summary");
              var targeturl = "";
              if (funcsum !== null) {
                targeturl = $(funcsum).attr("targeturl");
              }
              ru.cesar.seeker.get_summary_show("", targeturl, instanceid);
              // Remove the save warning
              $('.save-warning').html("");
              break;
            case "openurl":
              // Open the URL provided in attribute 'openurl'
              window.location.href = openurl;
              break;
            default:
              // Indicate we are loading
              $(".save-warning").html("Updating item... " + instanceid.toString());
              // Make a GET call with fresh data
              data = [];
              data.push({ 'name': 'instanceid', 'value': instanceid });
              // Add parameters depending on the openid
              switch (openid) {
                case "result_container_3":
                  // Need to add the 'qc_select' value
                  var iQcSelect = $("#qc_select").val();
                  data.push({ 'name': 'qc_select', 'value': iQcSelect });
                  break;
              }
              // Make an AJAX call to get an existing or new specification element HTML code
              response = ru.cesar.seeker.ajaxcall(ajaxurl, data, "GET");
              if (response !== undefined && response.status && response.status === 'ok') {
                // Load the new data
                $(elOpen).html(response.html);
                // Make sure events are set again
                ru.cesar.seeker.init_events();
                switch (openid) {
                  case "research_container_42":
                    // add any event handlers for wizard part '42'
                    ru.cesar.seeker.init_cvar_events();
                    break;
                  case "research_container_43":
                  case "research_container_44":
                  case "research_container_62":
                  case "research_container_63":
                  case "research_container_72":
                  case "research_container_73":
                    // add any event handlers for wizard part '43' and '44' and '62'
                    ru.cesar.seeker.init_arg_events();
                    break;
                  case "research_container_6":
                    // add any event handlers for wizard part '46'
                    ru.cesar.seeker.init_cond_events();
                    break;
                  case "research_container_7":
                    // add any event handlers for wizard part '46'
                    ru.cesar.seeker.init_feat_events();
                    break;
                }
              }
              break;
          }
          

          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);

          // Stop waiting
          private_methods.waitStop(elWait);
        } catch (ex) {
          private_methods.errMsg("ajaxform_click", ex);
          // Stop waiting
          private_methods.waitStop(elWait);
        }
      },

      /**
       * ajaxform_load
       *   General way to load an ajax form for 'New' or 'Edit' purposes
       *
       */
      ajaxform_load: function (ajaxurl, instanceid, data) {
        var response = {},
            html = "";      // The HTML code to be put

        try {
          // Initial response
          response['status'] = "none";
          // See if data needs to be initialized
          if (data === undefined) {
            data = [];      // Array to store the POST data
          }
          // Store the instanceid
          // data.push({ 'name': 'object_id', 'value': instanceid });

          // If there is an instance ID, then make sure the URL ends with that id
          if (instanceid !== undefined && instanceid !== '' && instanceid !== "None" ) {
            // First check if we already have a sequence of /nnn/
            if (!/\/\d+\//.test(ajaxurl) && ajaxurl.indexOf('/' + instanceid + "/") < 0) {
              ajaxurl += instanceid + "/";
            }
          }

          // NOTE: the form data will be fetched in the Python Server part
          // Make an AJAX GET call to get the correct HTML code
          $.ajax({
            url: ajaxurl,
            type: "GET",
            data: data,
            async: false,
            dataType: 'json',
            success: function (data) {
              // Take over the JSON response (consisting of 'status' and 'html')
              response = data;
              // Make sure events are set again
              ru.cesar.seeker.init_events();
              var x = 1;
            },
            failure: function () {
              response['status'] = "error";
              response['html'] = "AJAX get failure";
            }
          });
          // REturn the response
          return response;
        } catch (ex) {
          private_methods.errMsg("ajaxform_load", ex);
          return {'status': 'error', 'html': ex.message};
        }
      },

      /**
       *  cloneMore
       *      Add a form to the formset
       *      selector = the element that should be duplicated
       *      type     = the formset type
       *      number   = boolean indicating that re-numbering on the first <td> must be done
       *
       */
      cloneMore: function (selector, type, number) {
        var elTotalForms = null,
            total = 0;

        try {
          // Clone the element in [selector]
          var newElement = $(selector).clone(true);
          // Find the total number of [type] elements
          elTotalForms = $('#id_' + type + '-TOTAL_FORMS').first();
          // Determine the total of already available forms
          if (elTotalForms === null) {
            // There is no TOTAL_FORMS for this type, so calculate myself
          } else {
            // Just copy the TOTAL_FORMS value
            total = $(elTotalForms).val();
          }

          // Find each <input> element
          newElement.find(':input').each(function () {
            // Get the name of this element, adapting it on the fly
            var name = $(this).attr("name").replace("__prefix__", total.toString());
            // Produce a new id for this element
            var id = $(this).attr("id").replace("__prefix__", total.toString());
            // Adapt this element's name and id, unchecking it
            $(this).attr({ 'name': name, 'id': id }).val('').removeAttr('checked');
          });
          newElement.find('select').each(function () {
            // Get the name of this element, adapting it on the fly
            var name = $(this).attr("name").replace("__prefix__", total.toString());
            // Produce a new id for this element
            var id = $(this).attr("id").replace("__prefix__", total.toString());
            // Adapt this element's name and id, unchecking it
            $(this).attr({ 'name': name, 'id': id }).val('').removeAttr('checked');
          });

          // Find each <label> under newElement
          newElement.find('label').each(function () {
            // Adapt the 'for' attribute
            var newFor = $(this).attr("for").replace("__prefix__", total.toString());
            $(this).attr('for', newFor);
          });

          // Look at the inner text of <td>
          newElement.find('td').each(function () {
            var elText = $(this).children().first();
            if (elText !== undefined) {
              var sHtml = $(elText).html();
              if (sHtml !== undefined && sHtml !== "") {
                sHtml = sHtml.replace("__counter__", total.toString());
                $(elText).html(sHtml);
              }
              // $(elText).html($(elText).html().replace("__counter__", total.toString()));
            }
          });
          // Look at the attributes of <a>
          newElement.find('a').each(function () {
            // Iterate over all attributes
            var elA = this;
            $.each(elA.attributes, function (i, attrib) {
              var attrText = $(elA).attr(attrib.name).replace("__counter__", total.toString());
              $(this).attr(attrib.name, attrText);
            });
          });


          // Adapt the total number of forms in this formset
          total++;
          $('#id_' + type + '-TOTAL_FORMS').val(total);

          // Adaptations on the new <tr> itself
          newElement.attr("id", "arguments-" + (total - 1).toString());
          newElement.attr("class", "form-row row" + total.toString());

          // Insert the new element before the selector = empty-form
          $(selector).before(newElement);

          // Should we re-number?
          if (number !== undefined && number) {
            // Walk all <tr> elements of the table
            var iRow = 1;
            $(selector).closest("tbody").children("tr.form-row").not(".empty-form").each(function () {
              var elFirstCell = $(this).find("td").not(".hidden").first();
              $(elFirstCell).html(iRow);
              iRow += 1;
            });
          }

          // Return the new <tr> 
          return newElement;

        } catch (ex) {
          private_methods.errMsg("cloneMore", ex);
          return null;
        }
      },

      /**
       * condtype_click
       *   Set the type of condition: dvar versus func
       *
       */
      condtype_click: function (el) {
        try {
          var elRow = (el.target === undefined) ? el : $(this).closest("tr");
          var elType = $(elRow).find(".cond-type").first();
          var elVal = $(elRow).find(".cond-val-exp").first();
          // Find the type element
          var elcondtype = $(elType).find("select").first();
          // Get its value
          var elcondtypeVal = $(elcondtype).val();
          // First hide everything
          $(elVal).children("div").children("span").addClass("hidden");
          $(elVal).children("div").children("div").addClass("hidden");
          // Hide/show, depending on the value
          switch (elcondtypeVal) {
            case "dvar": // Data-dependant variable
              $(elVal).find(".cond-dvar").removeClass("hidden");
              break;
            case "func": // Function
              $(elVal).find(".cond-expression").removeClass("hidden");
              break;
            case "json":  // Upload JSON function definition
              $(elVal).find(".cond-json").removeClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("condtype_click", ex);
        }
      },

      /**
       * corpus_choice
       *   Process the chosen corpus-part and show the result
       *
       */
      corpus_choice : function(el, sTarget) {
        var divTarget = "",
            divOption = null, // Chosen <option>
            sLanguage = "",   // Chosen language
            sPart = "",       // Chosen corpus part
            sHtml = "",
            iChosen = 0,      // ID of chosen one
            sChosen = "";     // Option that has been chosen

        try {
          // Get the target <div>
          divTarget = "#" + sTarget;
          // Find out what has been chosen
          sChosen = $("#select_part").val();
          if (sChosen !== undefined && sChosen !== "" && sChosen !== "-") {
            // Also set the [searchPart] parameter
            $("#searchPart").attr("value", sChosen);
            // Get the integer that has been chosen
            iChosen = parseInt(sChosen, 10);
            divOption = $("#select_part").find("option[value=" + iChosen + "]");
            if (divOption !== undefined && divOption !== null) {
              sPart = $(divOption).text();
              sLanguage = $(divOption).closest("optgroup").attr("label");
              sHtml = "<div class='col-md-12'><table class='seeker-choice'><tr><td>Language: </td><td class='b'>" + sLanguage + "</td></tr>" +
                "<tr><td>Corpus (part):</td><td class='b'>" + sPart + "</td></tr></table></div>";
              $(divTarget).html(sHtml);

              // TODO: Check whether this search has already been made
            }
          }

        } catch (ex) {
          private_methods.errMsg("corpus_choice", ex);
        }
      },

      /**
       * corpus_refine
       *   Refine search selection
       *
       */
      corpus_refine: function (el, sTarget) {
        var divTarget = "",
            divOption = null, // Chosen <option>
            sChosen = "";     // Option that has been chosen

        try {
          // Get the target <div>
          divTarget = "#" + sTarget;
          // Find out what has been chosen
          sChosen = $(el).val();
          if (sChosen !== undefined && sChosen !== "") {
            switch (sChosen) {
              case "-":
              case "all":
                // Hide the target
                $(divTarget).addClass("hidden");
                break;
              default:
                // Show the target
                $(divTarget).removeClass("hidden");
                break;
            }
          }

        } catch (ex) {
          private_methods.errMsg("corpus_refine", ex);
        }
      },

      /**
       * cvartype_click
       *   Set the type of construction variable: fixed value or calculate
       *
       *   Assumptions:
       *    0 = fixed value
       *    1 = expression (function)
       *    2 = global variable
       *
       */
      cvartype_click: function (el) {
        try {
          var elRow = (el.target === undefined) ? el : $(this).closest("tr");
          var elType = $(elRow).find(".cvar-type").first();
          var elVal = $(elRow).find(".cvar-val-exp").first();
          // Find the type element
          var elCvarType = $(elType).find("select").first();
          // Get its value
          var elCvarTypeVal = $(elCvarType).val();
          // First hide everything
          $(elVal).children("div").children("span").addClass("hidden");
          $(elVal).children("div").children("div").addClass("hidden");
          // Hide/show, depending on the value
          switch (elCvarTypeVal) {
            case "fixed": // Fixed value
              $(elVal).find(".cvar-value").removeClass("hidden");
              break;
            case "calc": // Expression
              $(elVal).find(".cvar-expression").removeClass("hidden");
              break;
            case "gvar": // Global variable
              $(elVal).find(".cvar-gvar").removeClass("hidden");
              break;
            case "json":  // Upload JSON function definition
              $(elVal).find(".cvar-json").removeClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("cvartype_click", ex);
        }
      },

      /**
       * cvarcalculate_click
       *   Show or hide the calculation of one data-specific variable for all search-elements
       *
       */
      cvarcalculate_click: function () {
        try {
          // Get the loopid 
          var loopid = $(this).attr("loopid");
          // Find the correct row
          var elCalcRow = $(this).closest("tbody").find("#" + loopid);
          // Is it closed or opened?
          if ($(elCalcRow).hasClass("hidden")) {
            // Unhide it
            $(elCalcRow).removeClass("hidden");
          } else {
            // Hide it
            $(elCalcRow).addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("cvarcalculate_click", ex);
        }
      },

      /**
       * cvarspecify_click
       *   Create a calculation form and show it to the user
       *
       */
      cvarspecify_click: function () {
        try {
          // Get the loopid to find out exactly where we are...
          var loopid = $(this).attr("loopid");
          var vardefid = $(this).attr("vardefid");
          var constructionid = $(this).attr("constructionid");
          // Find the correct row
          var elCalcRow = $(this).closest("tbody").find("#" + loopid);
          // Is it closed or opened?
          if ($(elCalcRow).hasClass("hidden")) {
            // Find the nearest [cvar-item]
            var elCvarItem = $(this).closest("tr").find(" td.hidden div input");
            // Get the id attribute
            var cvarId = $(elCvarItem).attr("id");
            // Make an AJAX call to get an existing or new specification element HTML code
            $.ajax({
              url: '/ajax/getspecel/',
              data: {
                'cvarid': cvarId, 'vardefid': vardefid, 'constructionid': constructionid
              },
              dataType: 'json',
              success: function (data) {
                if (data.status && data.status === 'ok') {
                  $(elCalcRow).html(data.specelform);
                  // Unhide it
                  $(elCalcRow).removeClass("hidden");
                }
              },
              failure: function () {
                var iStop = 1;
              }
            });
          } else {
            // Hide it
            $(elCalcRow).addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("cvarspecify_click", ex);
        }
      },

      /**
       * feattype_click
       *   Set the type of feature: dvar versus func
       *
       */
      feattype_click: function (el) {
        try {
          var elRow = (el.target === undefined) ? el : $(this).closest("tr");
          var elType = $(elRow).find(".feat-type").first();
          var elVal = $(elRow).find(".feat-val-exp").first();
          // Find the type element
          var elfeattype = $(elType).find("select").first();
          // Get its value
          var elfeattypeVal = $(elfeattype).val();
          // First hide everything
          $(elVal).children("div").children("span").addClass("hidden");
          $(elVal).children("div").children("div").addClass("hidden");
          // Hide/show, depending on the value
          switch (elfeattypeVal) {
            case "dvar": // Data-dependant variable
              $(elVal).find(".feat-dvar").removeClass("hidden");
              break;
            case "func": // Function
              $(elVal).find(".feat-expression").removeClass("hidden");
              break;
            case "json":  // Upload JSON function definition
              $(elVal).find(".feat-json").removeClass("hidden");
              break;
          }
        } catch (ex) {
          private_methods.errMsg("feattype_click", ex);
        }
      },

      /**
       *  funcdefshow
       *      Show the function definition
       *
       */
      funcdefshow: function (el, sMyClass) {
        var elTr = null,
            sClass = "function-details";

        try {
          if (sMyClass !== undefined && sMyClass !== "") {
            sClass = sMyClass;
          }
          // Get to the nearest <tr>
          elTr = $(el).closest("tr");
          // Get to the next row
          elTr = $(elTr).nextAll("."+sClass).first();
          // Check its status
          if ($(elTr).hasClass("hidden")) {
            // Hide all other [function-details]
            $(elTr).closest("table").find("." + sClass).addClass("hidden");
            // It's hidden, so open it
            $(elTr).removeClass("hidden");
          } else {
            // It's open, so close it
            $(elTr).addClass("hidden");
          }


        } catch (ex) {
          private_methods.errMsg("funcdefshow", ex);
        }
      },

      /**
       * get_summary_click
       *   Show or hide the summary of the expression here
       *
       */
      get_summary_click: function (el, target, bShow) {
        var response,   // The ID of the current row
            targeturl = "",
            sTargetId = "#cvar_summary";

        try {
          // Possibly get target
          if (target !== undefined && target !== "") {
            sTargetId = target;
          }
          // Get to the row from here
          var elRow = $(el).closest("tr");
          // Find the expression summary
          var elSum = $(sTargetId);
          // Store the target url
          targeturl = $(el).attr("targeturl");
          // Is it closed or opened?
          if ($(elSum).hasClass("hidden") || (bShow !== undefined && bShow)) {
            ru.cesar.seeker.get_summary_show(sTargetId, targeturl);
          } else {
            // Hide it
            $(elSum).addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("get_summary_click", ex);
        }
      },

      /**
       * get_summary_click
       *   Show the summary of the expression fetched from [targeturl]
       *
       */
      get_summary_show: function (target, targeturl, instanceid) {
        var response,   // The ID of the current row
            elSum = null,
            elInstance = null,
            sTargetId = "#cvar_summary";

        try {
          // Possibly get target
          if (target !== undefined && target !== "") {
            sTargetId = target;
          }
          // Find the expression summary
          elSum = $(sTargetId);
          // Calculate and show the value
          response = ru.cesar.seeker.ajaxform_load(targeturl);
          if (response.status && response.status === "ok") {
            // Make the HTML response visible
            $(elSum).html(response.html);
            // Make sure events are set again
            ru.cesar.seeker.init_events();
          }
          // Copy the 'targeturl' attribute
          if (targeturl !== undefined && targeturl !== "") {
            // Add the targeturl to the summary element
            $(elSum).attr('targeturl', targeturl);
          }
          // Unhide it
          $(elSum).removeClass("hidden");
          // Has an instanceid been specified?
          if (instanceid !== undefined && instanceid !== "") {
            // Find the element with this instanceid
            elInstance = $(elSum).find("[instanceid='" + instanceid + "']").first();
            if (elInstance !== null) {
              // Show this one and all those above it
              $(elInstance).parents(".func-view").removeClass("hidden");
            }
          }
        } catch (ex) {
          private_methods.errMsg("get_summary_show", ex);
        }
      },

      /**
       * sync_process
       *    Process a synchronisation request
       * 
       * @param {type} synctype
       */
      sync_process: function (syncurl, synctype, targetdiv) {
        var syncdata = [{'name': 'synctype', 'value': synctype}];
        // Start asking for the status
        $.get(syncurl, syncdata, function (response) {
          // First leg has been done
          if (response === undefined || response === null || !("status" in response)) {
            private_methods.errMsg("No status returned");
          } else {
            switch (response.status) {
              case "ok":
              case "ready":
              case "finished":
                $(targetdiv).html("ready");
                break;
              case "error":
                $(targetdiv).html(response['msg']);
                break;
              default:
                // SHow the status
                $(targetdiv).html(response['status'] + ": " + response['msg']);
                // make sure to ask for status again
                setTimeout(function () { ru.cesar.seeker.sync_process(syncurl, synctype, targetdiv); }, 1000);
                break;
            }
          }
        });
      },

      /**
       * import_post
       *    Input data from a post form
       * 
       */
      import_post: function (el) {
        var frm = null,
            data = [],
            more = {},
            synctype = "",
            idx = 0,
            filefield = null,
            elInput = null,   // The <input> element with the files_field
            elProg = null,    // The progress bar
            targeturl = "",
            targetid = "",    // The div where the uploaded reaction comes
            statusid = "",    // The div where the status in-between appears
            sSaveDiv = "",    // Where to go if saving is needed
            syncurl = "",
            sMsg = "";

        try {
          private_methods.errClear();
          // Get information
          frm = $(el).closest("form")
          targeturl = $(el).attr("targeturl");
          targetid = "#" + $(el).attr("targetid");
          syncurl = $(el).attr("syncurl");
          idx = syncurl.indexOf("=");
          if (idx > 0) {synctype = syncurl.split("=")[1];}
          elProg = $("#" + synctype + "-import_progress");
          statusid = "#" + synctype + "-import_status";

          // CLear previous stuff
          $(targetid).html("");

          // Gather data and it needs to be in an object
          frm = $(el).closest("form");
          data = frm.serializeArray();
          for (var i = 0; i < data.length; i++) {
            more[data[i]['name']] = data[i]['value'];
          }
          // The <input> element with the file
          elInput = $(frm).find("input[type='file']").first();

          // Show progress
          $(elProg).attr("value", "0");
          $(elProg).removeClass("hidden");

          if (syncurl !== undefined && syncurl !== "") {
            // Start off Status reading here
            setTimeout(function () { ru.cesar.seeker.sync_process(syncurl, synctype, statusid); }, 2000);
          }

          // Upload file and other (form) data
          $(elInput).upload(targeturl,
            more,
            function (response) {
              // First leg has been done
              if (response === undefined || response === null || !("status" in response)) {
                private_methods.errMsg("No status returned");
              } else {
                switch (response.status) {
                  case "ok":
                    if ("html" in response) {
                      $(targetid).html(response['html']);
                    }
                    break;
                  case "error":
                    if ("html" in response) {
                      //private_methods.errMsg("error: " + response['html']);
                      $(targetid).html("<code>" + response['html'] + "</code>");
                      if ($(targetid).find(".errors").html().trim() === "") {
                        $(targetid).html("<code>Error</code>");
                      }
                    } else {
                      $(targetid).html("<code>See the error description</code>");
                    }
                    break;
                }
              }
            }, function (progress, value) {
              // Show  progress of uploading to the user
              console.log(progress);
              $(elProg).val(value);
            }
          );
          // Hide progress after some time
          setTimeout(function () { $(elProg).addClass("hidden"); }, 1000);
              
 /*             
          $.post(targeturl, data, function (response) {
            // First leg has been done
            if (response === undefined || response === null || !("status" in response)) {
              private_methods.errMsg("No status returned");
            } else {
              switch (response.status) {
                case "ok":
                  if ("html" in response) {
                    $(targetid).html(response['html']);
                  }
                  break;
                case "error":
                  if ("html" in response) {
                    private_methods.errMsg("error: " + response['html']);
                    $(targetid).html(response['html']);
                  }
                  break;
              }
            }
          });*/

        } catch (ex) {
          private_methods.errMsg("import_post", ex);
        }
      },

      /**
       * import_data
       *   Allow user to upload a file
       *
       * Assumptions:
       * - the [el] contains parameter  @targeturl
       * - there is a div 'import_progress'
       * - there is a div 'id_{{ftype}}-{{forloop.counter0}}-file_source'
       *
       */
      import_data: function (sKey) {
        var frm = null,
            targeturl = "",
            fdata = null,
            el = null,
            elProg = null,    // Progress div
            elErr = null,     // Error div
            data = null,
            xhr = null,
            files = null,
            sFtype = "",      // Type of function (cvar, feat, cond)
            elWait = null,
            bDoLoad = false,  // Need to load with a $.get() afterwards
            elInput = null,   // The <input> element with the files
            more = {},        // Additional (json) data to be passed on (from form-data)
            sTargetDiv = "",  // The div where the uploaded reaction comes
            sSaveDiv = "",    // Where to go if saving is needed
            sMsg = "";

        try {
          // The element to use is the key + import_info
          el = $("#" + sKey + "-import_info");
          elProg = $("#" + sKey + "-import_progress");
          elErr = $("#" + sKey + "-import_error");

          // Set the <div> to be used for waiting
          elWait = private_methods.waitInit(el);

          // Get the URL
          targeturl = $(el).attr("targeturl");
          sTargetDiv = $(el).attr("targetid");
          sSaveDiv = $(el).attr("saveid");

          if (targeturl === undefined && sSaveDiv !== undefined && sSaveDiv !== "") {
            targeturl = $("#" + sSaveDiv).attr("ajaxurl");
            sTargetDiv = $("#" + sSaveDiv).attr("openid");
            sFtype = $(el).attr("ftype");
            bDoLoad = true;
          }

          if ($(el).is("input")) {
            elInput = el;
          } else {
            elInput = $(el).find("input").first();
          }

          // Show progress
          $(elProg).attr("value", "0");
          $(elProg).removeClass("hidden");
          if (bDoLoad) {
            $(".save-warning").html("loading the definition..." + loc_sWaiting);
            $(".submit-row button").prop("disabled", true);
          }

          // Add data from the <form> nearest to me: 
          frm = $(el).closest("form");
          if (frm !== undefined) { data = $(frm).serializeArray(); }

          for (var i = 0; i < data.length; i++) {
            more[data[i]['name']] = data[i]['value'];
          }
          // Showe the user needs to wait...
          private_methods.waitStart(elWait);

          // Upload XHR
          $(elInput).upload(targeturl,
            more,
            function (response) {
              // Transactions have been uploaded...
              console.log("done: ", response);

              // Show where we are
              $(el).addClass("hidden");
              $(".save-warning").html("saving..." + loc_sWaiting);

              // First leg has been done
              if (response === undefined || response === null || !("status" in response)) {
                private_methods.errMsg("No status returned");
              } else {
                switch (response.status) {
                  case "ok":
                    // Check how we should react now
                    if (bDoLoad) {
                      // Show where we are
                      $(".save-warning").html("retrieving..." + loc_sWaiting);

                      $.get(targeturl, function (response) {
                        if (response === undefined || response === null || !("status" in response)) {
                          private_methods.errMsg("No status returned");
                        } else {
                          switch (response.status) {
                            case "ok":
                              // Show the response in the appropriate location
                              $("#" + sTargetDiv).html(response.html);
                              $("#" + sTargetDiv).removeClass("hidden");
                              break;
                            default:
                              // Check how/what to show
                              if ("err_view" in response) {
                                private_methods.errMsg(response['err_view']);
                              } else if ("error_list" in response) {
                                private_methods.errMsg(response['error_list']);
                              } else {
                                // Just show the HTML
                                $("#" + sTargetDiv).html(response.html);
                                $("#" + sTargetDiv).removeClass("hidden");
                              }
                              break;
                          }
                          // Make sure events are in place again
                          ru.cesar.seeker.init_events();
                          switch (sFtype) {
                            case "cvar":
                              ru.cesar.seeker.init_cvar_events();
                              break;
                            case "cond":
                              ru.cesar.seeker.init_cond_events();
                              break;
                            case "feat":
                              ru.cesar.seeker.init_feat_events();
                              break;
                          }
                          // Indicate we are through with waiting
                          private_methods.waitStop(elWait);
                        }
                      });
                    } else {
                      // Remove all project-part class items
                      $(".project-part").addClass("hidden");
                      // Place the response here
                      $("#" + sTargetDiv).html(response.html);
                      $("#" + sTargetDiv).removeClass("hidden");
                    }
                    break;
                  default:
                    // Check WHAT to show
                    sMsg = "General error (unspecified)";
                    if ("err_view" in response) {
                      sMsg = response['err_view'];
                    } else if ("error_list" in response) {
                      sMsg = response['error_list'];
                    } else {
                      // Indicate that the status is not okay
                      sMsg = "Status is not good. It is: " + response.status;
                    }
                    // Show the message at the appropriate location
                    $(elErr).html("<div class='error'>" + sMsg + "</div>");
                    // Make sure events are in place again
                    ru.cesar.seeker.init_events();
                    switch (sFtype) {
                      case "cvar":
                        ru.cesar.seeker.init_cvar_events();
                        break;
                      case "cond":
                        ru.cesar.seeker.init_cond_events();
                        break;
                      case "feat":
                        ru.cesar.seeker.init_feat_events();
                        break;
                    }
                    // Indicate we are through with waiting
                    private_methods.waitStop(elWait);
                    $(".save-warning").html("(not saved)");
                    break;
                }
              }
              private_methods.waitStop(elWait);
            }, function (progress, value) {
              // Show  progress of uploading to the user
              console.log(progress);
              $(elProg).val(value);
            }
          );
          // Hide progress after some time
          setTimeout(function () { $(elProg).addClass("hidden"); }, 1000);

          // Indicate waiting can stop
          private_methods.waitStop(elWait);
        } catch (ex) {
          private_methods.errMsg("import_data", ex);
          private_methods.waitStop(elWait);
        }
      },

      /**
       *  init_arg_events
       *      Bind events to work with function arguments
       *
       */
      init_arg_events: function () {
        try {
          // Make sure the 'Type' field values are processed everywhere
          $(".arg-item").each(function () {
            // Perform the same function as if we were clicking it
            ru.cesar.seeker.argtype_click(this);
          });
          // Specify the change reaction function
          $(".arg-type select").change(ru.cesar.seeker.argtype_click);
        } catch (ex) {
          private_methods.errMsg("init_arg_events", ex);
        }
      },

      /**
       *  init_simple_events
       *      Bind events to work with the simple form
       *
       */
      init_simple_events: function () {
        var sEvTypes = "change paste input";

        try {
          // Bind one 'tabular_deletrow' event handler to clicking that button
          $(".delete-row").unbind("click");
          $('tr td a.delete-row').click(ru.cesar.seeker.tabular_deleterow);

          // Make sure the initial names are stored
          ru.cesar.seeker.simple_store_names();

          // Bind the correct name-change handler to related name change
          $(".rel-name").unbind(sEvTypes);
          $("tr.rel-form td.rel-name input").on(sEvTypes,
            function () { ru.cesar.seeker.simple_names_update(this, "input"); }
            );

          //$(".delete-row").click(function (elThis) { ru.cesar.seeker.tabular_deleterow(); });
        } catch (ex) {
          private_methods.errMsg("init_simple_events", ex);
        }
      },

      /**
       *  simple_names_update
       *      Update the names and corresponding 'Towards' list in all rows of simple
       *
       */
      simple_names_update: function (elThis, sType) {
        var i = 0,
            oRelated = {},
            sVarPrev = "",    // Previous name
            sVarName = "",    // New name
            sVarId = "";

        try {
          switch (sType) {
            case "input":
              // This is an event on the [input] for simple_names
              // Make sure no space gets inserted
              sVarName = $(elThis).val();
              if (sVarName.indexOf(" ") >= 0) {
                $("#simple_modifying").html("<code>ERROR</code>: remove space in [" + sVarName + "]");
                loc_bSimpleNameError = true;
              } else {
                $("#simple_modifying").html("");
                loc_bSimpleNameError = false;
                // Everything is okay: make sure changes ripple through 'down'
                sVarId = $(elThis).attr("id");
                // Look for this id/name in the related table
                for (i = 0; i < loc_related.length; i++) {
                  oRelated = loc_related[i];
                  if (oRelated['varid'] === sVarId) {
                    // We have the correct variable: Note the previous name
                    sVarPrev = oRelated['varname'];
                    break;
                  }
                }
                // Emend the name in the towards tables
                if (sVarPrev !== "") {
                  ru.cesar.seeker.simple_store_names(sVarPrev, sVarName);
                }
              }
              break;
          }

        } catch (ex) {
          private_methods.errMsg("simple_names_update", ex);
        }
      },

      /**
       *  simple_update
       *      Update the 'Towards' list in all rows of simple
       *
       */
      simple_update: function () {
        var elRelated = "#related_constituents",
            elTowards = null,
            elName = "",
            sKey = "",
            sValue = "",
            sName = "",
            sInsert = "",
            sSelected = "",
            i = 0,
            lNames = [{ name: "search", "value": "Search Hit" }],
            lHtml = [],
            lRow = [];

        try {
          // walk the rows of the table
          $(elRelated).find("tr.form-row").not(".empty-form").each(function (idx, elRow) {
            // Add the row information to this item
            elName = $(elRow).find(".rel-name input").first();
            elTowards = $(elRow).find(".rel-towards select").first();
            // Get the currently selected name
            sSelected = $(elTowards).val();

            // Adapt class
            if (!$(elRow).hasClass("rel-form")) {
              $(elRow).addClass("rel-form");
            }

            // Process the list of names so far
            lHtml = [];
            sName = "search";
            for (i = 0; i < lNames.length; i++) {
              sKey = lNames[i]['name'];
              sValue = lNames[i]['value'];
              sInsert = (sSelected === sKey) ? "selected=\"selected\" " : "";
              lHtml.push("<option value=\"" + sKey + "\" " + sInsert + ">" + sValue + "</option>");
            }
            // Adapt the select box
            $(elTowards).html(lHtml.join("\n"));

            // Get the name of this variable
            sName = $(elName)[0].value;

            // Add the new name to the list
            lNames.push({ name: sName, value: sName });
          });

          // Update names
          ru.cesar.seeker.simple_store_names();

          // Update viewing
          ru.cesar.seeker.related_view(elRelated);

        } catch (ex) {
          private_methods.errMsg("simple_update", ex);
        }
      },

      /**
       *  simple_store_names
       *      Store all the names in variables of simple-related
       *
       */
      simple_store_names: function (sPrev, sNew) {
        var elRelated = "#related_constituents",
            elTowards = null,
            elName = "",
            sName = "",
            sNameId = "",
            sSelected = "",
            lRow = [];

        try {
          // EMpty the current array
          loc_towards = [{ name: "search", "value": "Search Hit" }];
          loc_related = [];

          // walk the rows of the table
          $(elRelated).find("tr.form-row").not(".empty-form").each(function (idx, elRow) {
            // Get the name of the variable
            elName = $(elRow).find(".rel-name input").first();

            // Possibly emend the [towards] contents
            if (sPrev !== undefined && sPrev !== "" && sNew !== undefined && sNew !== "") {
              // Find and change the variable in the towards table
              $(elRow).find(".rel-towards option").each(function (j, elT) {
                if ($(elT)[0].value === sPrev) {
                  $(elT).val(sNew);
                  $(elT).html(sNew);
                }
              });
            }

            // Get the currently selected name
            elTowards = $(elRow).find(".rel-towards select").first();
            sSelected = $(elTowards).val();

            // Get the name of this variable
            sName = $(elName)[0].value;
            sNameId = $(elName).attr("id");

            // Add the new name to the list
            loc_towards.push({ name: sName, value: sName });

            // Update the full 'related' information of this line
            loc_related.push({line: idx, varname: sName, varid: sNameId, towards: sSelected });

          });

        } catch (ex) {
          private_methods.errMsg("simple_update", ex);
        }
      },

      /**
       *  init_cond_events
       *      Bind events to work with conditions
       *
       */
      init_cond_events: function () {
        try {
          // Make sure the 'Type' field values are processed everywhere
          $(".cond-item").each(function () {
            // Perform the same function as if we were clicking it
            ru.cesar.seeker.condtype_click(this);
          });
          // Specify the change reaction function
          $(".cond-type select").change(ru.cesar.seeker.condtype_click);
          // Specify the function to be called when the user presses "summary"
          $(".func-summary").unbind('click');
          $(".func-summary").click(function () { ru.cesar.seeker.get_summary_click(this, "#cond_summary"); });
        } catch (ex) {
          private_methods.errMsg("init_cond_events", ex);
        }
      },

      /**
       *  init_feat_events
       *      Bind events to work with featitions
       *
       */
      init_feat_events: function () {
        try {
          // Make sure the 'Type' field values are processed everywhere
          $(".feat-item").each(function () {
            // Perform the same function as if we were clicking it
            ru.cesar.seeker.feattype_click(this);
          });
          // Specify the change reaction function
          $(".feat-type select").change(ru.cesar.seeker.feattype_click);
          // Specify the function to be called when the user presses "summary"
          $(".func-summary").unbind('click');
          $(".func-summary").click(function () { ru.cesar.seeker.get_summary_click(this, "#feat_summary"); });
        } catch (ex) {
          private_methods.errMsg("init_feat_events", ex);
        }
      },

      /**
       *  init_cvar_events
       *      Bind events to work with constituent variables
       *
       */
      init_cvar_events: function () {
        try {
          // Specify the function to be called when the user presses [Calculation...]
          $(".cvar-calculate").click(ru.cesar.seeker.cvarcalculate_click);
          // Specify the function to be called when the user presses [Calculation...]
          $(".cvar-specify").click(ru.cesar.seeker.cvarspecify_click);
          // Make sure the 'Type' field values are processed everywhere
          $(".cvar-item").each(function () {
            // Perform the same function as if we were clicking it
            ru.cesar.seeker.cvartype_click(this);
          });
          // Specify the change reaction function
          $(".cvar-type select").change(ru.cesar.seeker.cvartype_click);
          // Specify the function to be called when the user presses "summary"
          $(".func-summary").click(function () { ru.cesar.seeker.get_summary_click(this, "#cvar_summary"); });
          // When the function-definition-selection changes, the button name should change
          $(".cvar-fundef select").change(function () {
            var button = $(this).closest(".cvar-expression").find("a.btn").first();
            if (button !== null) {
              $(button).html("create");
            }
          });
        } catch (ex) {
          private_methods.errMsg("init_cvar_events", ex);
        }
      },

      /**
       *  click_if_new
       *      If the [divObject] is empty, then click on [sTarget]
       *
       */
      click_if_new: function (divObject, sTarget) {
        try {
          if (divObject !== undefined && sTarget !== undefined) {
            var sContent = $("#" + divObject).text().trim();
            if (sContent === "" || sContent === "None") {
              $("#" + sTarget).click();
            }
          }
        } catch (ex) {
          private_methods.errMsg("click_if_new", ex);
        }
      },

      /**
       *  form_row_select
       *      Select or unselect a form-row
       *
       */
      form_row_select: function () {
        var elTable = null,
            elRow = null,     // The row
            iSelCount = 0,    // Number of selected rows
            bSelected = false;

        try {
          // Get to the row
          elRow = $(this).closest("tr.form-row");
          // Get current state
          bSelected = $(elRow).hasClass("selected");
          // FInd nearest table
          elTable = $(elRow).closest("table");
          // Check if anything other than me is selected
          iSelCount = 1;
          // Remove all selection
          $(elTable).find(".form-row.selected").removeClass("selected");
          // CHeck what we need to do
          if (bSelected) {
            // We are de-selecting: hide the 'Up' and 'Down' buttons if needed
            ru.cesar.seeker.show_up_down(this,false);
          } else {
            // Select the new row
            $(elRow).addClass("selected");
            // SHow the 'Up' and 'Down' buttons if needed
            ru.cesar.seeker.show_up_down(this,true);
          }

        } catch (ex) {
          private_methods.errMsg("form_row_select", ex);
        }
      },

      /**
       *  show_up_down
       *      Show or hide up/down buttons
       *      But only do this if the table has a row that has elements with class ".var-order"
       *
       */
      show_up_down: function (el, bShow) {
        var bHasOrder = false,  // THis table has 'order'
            divSubmit = null,   // Submit row
            divUp = null,       // Button to move up
            divDown = null;     // Button to move down

        try {
          // DO we have order?
          bHasOrder = ($(el).closest("table").find(".var-order").first().length > 0);
          if (!bHasOrder) { return; }
          // We have order: find the buttons
          divSubmit = $(el).closest("form").find("div.submit-row").first();
          if (divSubmit.length === 0) { return;}
          divUp = $(divSubmit).find("span.row-up").first();
          divDown = $(divSubmit).find("span.row-down").first();
          // Check out the buttons
          if (divUp.length === 0) {
            // Create an UP button
            $(divSubmit).prepend("<span class='btn btn-primary row-up glyphicon glyphicon-chevron-up' title='move upwards'></span>");
            divUp = $(divSubmit).find("span.row-up").first();
            // bind click event
            $(divUp).on("click", function () {
              private_methods.var_move(this, 'up', 'selected');
            });
          }
          if (divDown.length === 0) {
            // create a DOWN button
            $(divSubmit).prepend("<span class='btn btn-primary row-down glyphicon glyphicon-chevron-down' title='move downwards'></span>");
            divDown = $(divSubmit).find("span.row-down").first();
            // bind click event
            $(divDown).on("click", function () {
              private_methods.var_move(this, 'down', 'selected');
            });
          }
          // We have order: show or hide buttons
          if (bShow) {
            // Show the buttons
            divUp.removeClass("hidden");
            divDown.removeClass("hidden");
          } else {
            // Hide the buttons
            divUp.addClass("hidden");
            divDown.addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("show_up_down", ex);
        }
      },

      /**
       *  init_events
       *      Bind main necessary events
       *
       */
      init_events: function () {
        try {
          // file selectors
          $(".btn-file input").on("change", function (e) {
            var fileName = '',
                $label = $(this).parent().next('span'),
                labelVal = 'Browse...';

            // Can we display the text ??
            if ($label !== undefined && $label.length > 0) {
              // Think of a text to display
              if (this.files && this.files.length > 1) {
                fileName = this.files.length + " files selected";
              } else if (e.target.value) {
                fileName = e.target.value.split('\\').pop();
              }
              // Actually display that text (if any)
              if (fileName) {
                $label.html(fileName);
              } else {
                $label.html(labelVal);
              }
            }
          });
          // Firefox bug fix
          $(".btn-file input").on('focus', function () { $(this).addClass('has-focus'); });
          $(".btn-file input").on('blur', function () { $(this).removeClass('has-focus'); });
          // NOTE: only treat the FIRST <a> within a <tr class='add-row'>
          //$('tr.add-row a').first().click(ru.cesar.seeker.tabular_addrow);
          $("tr.add-row").each(function () {
            $(this).find("a").first().unbind('click').click(ru.cesar.seeker.tabular_addrow);
          }); 
          $(".delete-row").unbind("click");
          $('tr td a.delete-row').click(ru.cesar.seeker.tabular_deleterow);
          $('.inline-group > div > a.btn').click(function () {
            var elGroup = null,
                elTabular = null,
                sStatus = "";

            // Get the tabular
            elTabular = $(this).parent().next(".tabular");
            if (elTabular !== null) {
              // Get the status of this one
              if ($(elTabular).hasClass("hidden")) {
                $(elTabular).removeClass("hidden");
              } else {
                $(elTabular).addClass("hidden");
              }
            }
          });
          $('span.td-toggle-textarea').unbind('click').click(ru.cesar.seeker.toggle_textarea_click);
          $('input.td-toggle-textarea').unbind('click').click(ru.cesar.seeker.toggle_textarea_click);
          // Make sure variable ordering is supported
          $('td span.var-down').unbind('click').click(ru.cesar.seeker.var_down);
          $('td span.var-up').unbind('click').click(ru.cesar.seeker.var_up);

          // Allow form-row items to be selected or unselected
          $('tr.form-row').not(".rel-form").each(function () {
            // Add it to the first visible cell
            $(this).find("td").not(".hidden").first().unbind('click').click(ru.cesar.seeker.form_row_select);
            // Make sure any other cells  that have an <input> or a <td-toggle-textarea> are set too
            $(this).find("td").not(".hidden").each(function () {
              if ($(this).find("input").length > 0 ||
                  $(this).find("span.td-toggle-textarea").length > 0) {
                $(this).unbind("click").click(ru.cesar.seeker.form_row_select);
              }
            });
          });

          // Make sure all <input> elements in a <form> are treated uniformly
          $("form:not(.noblurring) input[type='text']").each(function () {
            var $this = $(this),
                has_js = false,
                $span = $this.prev("span");
            // Create span if not existing
            if ($span === undefined || $span === null || $span.length === 0) {
              $span = $this.before("<span></span");
              // Still need to go to the correct function
              $span = $this.prev("span");
            }

            // Set the value of the span
            if ($this.html().indexOf("<script") < 0 && $this.val().indexOf("<script") < 0) {
              $span.html($this.val());
            } else {
              $span.html("Remove_your_JS");
              has_js = true;
              $this.addClass("noblurring");
            }

            if (!has_js) {
              // Now specify the action on clicking the span
              $span.on("click", function () {
                var $this = $(this);
                $this.hide().siblings("input").show().focus().select();
              });
              // Specify what to do on blurring the input
              $this.on("blur", function () {
                var $this = $(this);
                if ($this.val().trim() !== "" && $this.val().indexOf("<script") < 0) {
                  // Show the value of the input in the span
                  $this.hide().siblings("span").text($this.val()).show();
                }
              })
              // Specify what to do on clicking in it
              $this.on("keydown", function (e) {
                // SPecify what to do if the tab is pressed
                if (e.which === 9) {
                  e.preventDefault();
                  if (e.shiftKey) {
                    // Need to go backwards
                    $(this).blur().closest("tr").prev("tr").find("input[type='text']").not(".hidden").first().prev("span").click();
                  } else {
                    // Move forwards
                    $(this).blur().closest("tr").next("tr").find("input[type='text']").not(".hidden").first().prev("span").click();
                  }
                }
              });
              // Make sure the <input> is hidden, unless it is empty
              if ($this.val().trim() !== "" && $this.html().trim() !== "") {
                $this.hide();
              }
            }
          });

          // Attach an event handler to all the NODES
          $("g.main-el").mouseover(function () { ru.cesar.seeker.main_info_show(this) });
          $("g.main-el").mouseout(function () { ru.cesar.seeker.main_info_hide(this) });

          // NOTE: do not use the following mouseout event--it is too weird to work with
          // $('td span.td-textarea').mouseout(ru.cesar.seeker.toggle_textarea_out);

          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);

          // Activate the EDITABLE interface (from passim)
          $(".ms.editable a").unbind("click").click(ru.cesar.seeker.process_edit);

        } catch (ex) {
          private_methods.errMsg("init_events", ex);
        }
      },

      /**
       * kwic_page
       *    Make sure we go to the indicated page
       * 
       * @param {type} iPage
       * @param {type} sFormDiv
       */
      kwic_page: function (iPage, sFormDiv) {
        var elStart = null;

        try {
          elStart = $("#"+sFormDiv);
          ru.cesar.seeker.load_kwic(elStart, iPage);
        } catch (ex) {
          private_methods.errMsg("kwic_page", ex);
        }
      },

      /**
       * load_kwic
       *   Make an AJAX request to load data for a Kwic instance
       * 
       * @param {dom}  elStart
       * @param {int}  iPage
       */
      load_kwic: function (elStart, iPage) {
        var data = [],
            targetid = "",
            waitid = "#kwic-fetch",
            ajaxurl = "",
            frm = null,
            response = null,
            instanceid = "";

        try {
          // Clear the errors
          private_methods.errClear();

          // obligatory parameter: ajaxurl
          //ajaxurl = $(elStart).attr("ajaxurl");
          //instanceid = $(elStart).attr("instanceid");
          ajaxurl = $(elStart).attr("targeturl");
          targetid = $(elStart).attr("targetid");

          // Gather the information
          frm = $(elStart).closest("form");
          if (frm !== undefined) { data = $(frm).serializeArray(); }

          //data.push({ 'name': 'instanceid', 'value': instanceid });
          data.push({ 'name': 'target', 'value': targetid });

          if (iPage === undefined) { iPage = 1; }
          data.push({ 'name': 'page', 'value': iPage });

          // Indicate we are waiting
          $(waitid).removeClass("hidden");
          // Define the post command
          var posting = $.post(ajaxurl, data);
          // Execute the post command and tell what needs to be done when ready
          posting.done(function (data) {
            // Put the results on display
            $("#"+targetid).html(data['html']);
            // Indicate we are ready
            $(waitid).addClass("hidden");
          });

        } catch (ex) {
          private_methods.errMsg("load_kwic", ex);
        }
      },

      /**
       * nowTime
       *   Get the current time as a string
       *
       */
      nowTime: function () {
        var now = new Date(Date.now());
        var sNow = now.getHours() + ":" + now.getMinutes() + ":" + now.getSeconds();
        return sNow;
      },

      /**
       *  toggle_prj_group
       *      Toggle the visibility of the current and following element
       *
       */
      toggle_prj_group: function (elThis) {
        var spanOne, spanTwo;

        try {
          // Get the following two <span> elements
          spanOne = $(elThis).next("span");
          spanTwo = $(spanOne).next("span");
          // Set visibility
          if ($(spanOne).hasClass("hidden")) {
            // Unhide it
            $(spanOne).removeClass("hidden");
            $(spanTwo).addClass("hidden");
          } else {
            // Hide it
            $(spanOne).addClass("hidden");
            $(spanTwo).removeClass("hidden");
          }

        } catch (ex) {
          private_methods.errMsg("toggle_prj_group", ex);
        }
      },

      /**
       *  part_detail_toggle
       *      Toggle part detail
       *
       */
      part_detail_toggle: function (iPk) {
        var sId = "";

        try {
          // validate
          if (iPk === undefined) return;
          // Get the name of the tag
          sId = "#part_details_" + iPk.toString();
          // Check if it is visible or not
          if ($(sId).hasClass("hidden")) {
            // Remove it
            $(sId).removeClass("hidden");
          } else {
            // Add it
            $(sId).addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("part_detail_toggle", ex);
        }
      },

      /**
       * show_related
       *    Set the 'related' button
       *
       */
      show_related: function (bShow) {
        var elAddRel = "#add_related";

        try {
          if (bShow) {
            $(elAddRel).attr("title", "Hide related");
            $(elAddRel).html("no related constituents");
          } else {
            $(elAddRel).attr("title", "Show related");
            $(elAddRel).html("related constituents");
          }
        } catch (ex) {
          private_methods.errMsg("show_related", ex);
        }

      },

      /**
       * init_simple
       *    Initialize the layout of simple
       *
       */
      init_simple: function () {
        var elSimple = "#search_mode_simple",
            elStart = "#search_mode_switch",
            elLabel = "#search_mode",
            elMore = "#simple_more",
            elRelated = "#related_constituents",
            elExtend = "#search_mode_extended",
            elForms = "#id_simplerel-TOTAL_FORMS",
            elTargetType = "#id_targetType",
            bDoRelated = false,
            iForms = 0;

        try {
          // Initially Hide related
          $(elRelated).addClass("hidden");
          //$(elRelated).html("related constituents");
          //$(elRelated).attr("title", "Show related");

          // Get the number of forms
          iForms = $(elForms).val();

          switch ($(elTargetType).val()) {
            case "e":
            case "c":
              // Make sure the the extended searching is shown
              $(".simple-search-2").removeClass("hidden");
              $(elMore).attr("title", "Let me specify less");
              $(elMore).html("less");
              // Check if [related_constituents] should be shown or not
              if (iForms > 0) {
                // Show related
                $(elRelated).removeClass("hidden");
                ru.cesar.seeker.show_related(true);
                bDoRelated = true;
              } else {
                ru.cesar.seeker.show_related(false);
              }
              break;
            case "w":
              // Make sure the the extended searching is hidden
              $(".simple-search-2").addClass("hidden");
              $(elMore).attr("title", "Let me specify more");
              $(elMore).html("more");
              // Check if [related_constituents] should be shown or not
              if (iForms > 0) {
                // Show related
                $(elRelated).removeClass("hidden");
                ru.cesar.seeker.show_related(true);
                bDoRelated = true;
              } else {
                ru.cesar.seeker.show_related(false);
              }
              break;
            case "q":
              // We should be in extended mode
              $(elStart).attr("title", "Switch to simple search");
              $(elLabel).html("Extended search");
              // Show extended
              $(elSimple).addClass("hidden");
              $(elExtend).removeClass("hidden");
              break;
          }

          // Check related
          if (bDoRelated) { ru.cesar.seeker.related_view(elRelated); }

          ru.cesar.seeker.init_simple_events();
        } catch (ex) {
          private_methods.errMsg("init_simple", ex);
        }
      },

      /**
       * related_view
       *    Try to show related (if all names are okay)
       *
       */
      related_view: function (elRelated) {
        try {
          // Treat all rows
          $(elRelated).find("tr.rel-form").not(".empty-form").each(function (i, el) {
            var lHtml = [],
                elForm = null,
                arName = [],
                sName = "",
                oForm = {},     // Key values
                oDisplay = {},  // Display values
                elName = $(el).find("td .kwname").first(),
                elDescr = $(el).find("td .rel-descr").first();

            // Put all the form element values into an array
            $(el).find("input, select").each(function (idx, elF) {
              arName = $(elF).attr("name").split("-");
              sName = arName[arName.length - 1];
              oForm[sName] = $(elF).val();
              if (elF.localName === "select") {
                oDisplay[sName] = $(elF).find("option:selected").text();
              } else {
                oDisplay[sName] = $(elF).val();
              }
            });

            // Initially we are okay
            loc_bRelated = true;

            // Check the name
            if (elName !== null && elName.length > 0) {
              // Get the value of the name
              sName = oForm['name'].trim();
              // Check the name
              if (sName === "") {
                // THis is serious business: no name means no go!
                loc_bRelated = false;
                loc_sRelatedErr = "GIVE A NAME";
                return false;
              }
              // Show the name
              $(elName).html(sName);
            }
            // Check the description
            if (elDescr !== null && elDescr.length > 0) {
              // Check for obligatory 'towards'
              if (oDisplay['towards'] === "") {
                // Serious business
                loc_bRelated = false;
                loc_sRelatedErr = "RELATED TO?";
                return false;
              }
              // Prepare our message
              if ('pos' in oForm && oForm['pos'] !== "") {
                lHtml.push("is the " + oDisplay["pos"]);
              } else {
                lHtml.push("is a");
              }
              // Obligatory: relation towards another constituent
              lHtml.push(" <b>" + oDisplay["raxis"] + "</b> of <span class=\"kwname\">" + oDisplay["towards"] + "</span>");
              // Optionally add syntactic category
              if (oForm["cat"] !== "") {
                lHtml.push("with category <span class=\"kwcat\">" + oForm["cat"] + "</span>");
              }
              // Optionally add text
              if (oForm["reltext"] !== "") {
                lHtml.push("with text like <span class=\"kwcat\">" + oForm["reltext"] + "</span>");
              }
              // Optionally add lemma
              if (oForm["rellemma"] !== "") {
                lHtml.push("with lemma <span class=\"kwcat\">" + oForm["rellemma"] + "</span>");
              }
              // Optional: skipping something
              if ('skip' in oForm && oForm['skip'] !== "") {
                lHtml.push(", skipping <b>" + oDisplay["skip"] + "</b>");
              }

              // Combine
              $(elDescr).html(lHtml.join(" "));
            }
          });
          // Make sure all is okay
          return loc_bRelated;
        } catch (ex) {
          private_methods.errMsg("related_view", ex);
        }
      },

      /**
       * switch_mode
       *    Switch between simple and extended search mode
       *
       */
      switch_mode: function (elStart, elLabel) {
        var elTargetType = "#id_targetType",
            elCql = "#id_searchcql",
            elRelated = "#related_constituents",
            elSimple = "#search_mode_simple",
            elExtend = "#search_mode_extended";

        try {
          if ($(elStart).attr("title").indexOf("extended") >= 0) {
            // Switch from simple to extended
            $(elStart).attr("title", "Switch to simple search");
            $(elLabel).html("Extended search");
            // Show extended
            $(elSimple).addClass("hidden");
            $(elExtend).removeClass("hidden");
          } else {
            // Switch from extended to simple
            $(elStart).attr("title", "Switch to extended search");
            $(elLabel).html("Simple search");
            // Show simple
            $(elSimple).removeClass("hidden");
            $(elExtend).addClass("hidden");
            // Clear CQL
            $(elCql).val("");
          }
        } catch (ex) {
          private_methods.errMsg("switch_mode", ex);
        }
      },

      /**
       * related_column
       *    Switch show/hide a column associated with 'related'
       *
       */
      related_column: function (elStart, sClass) {
        var elTarget = null,
            elFirst = null;

        try {
          // Get the target column
          elTarget = $("table tr " + sClass);
          if (elTarget.length > 0) {
            elFirst = elTarget[0];
            if ($(elFirst).hasClass("hidden")) {
              // SHow them
              $(elTarget).removeClass("hidden");
            } else {
              // Hide them
              $(elTarget).addClass("hidden");
            }
          }

        } catch (ex) {
          private_methods.errMsg("related_column", ex);
        }
      },

      /**
       * related_switch
       *    Switch show/hide the 'related constituents' for simple search view
       *
       */
      related_switch: function (elStart, sTarget, sType) {
        var elTarget = "#" + sTarget,
            elForms = "#id_simplerel-TOTAL_FORMS";
            
        try {
          if ($(elTarget).hasClass("hidden")) {
            // From hidden to SHOW
            $(elTarget).removeClass("hidden");
            ru.cesar.seeker.show_related(true);
          } else {
            // From showing to HIDDEN
            $(elTarget).addClass("hidden");
            ru.cesar.seeker.show_related(false);
            // Remove all rows that are filled -- except the EMPTY form
            $(".rel-form").not(".empty-form").remove();

            // Also reset the number of forms
            $(elForms).val("0");

            // Modify the simple search at the server
            ru.cesar.seeker.simple_modify(elStart);
          }

        } catch (ex) {
          private_methods.errMsg("related_switch", ex);
        }
      },

      /**
       * simple_switch
       *    Switch in the simple search view
       *
       */
      simple_modify: function (elStart) {
        var targeturl = "",
            elMsg = "#simple_modifying",
            data = [],
            frm = null;

        try {
          // Get the closest form
          frm = $(elStart).closest("form");
          if (frm !== undefined) {
            data = $(frm).serializeArray();
          }

          // Modify the simple search in the server
          targeturl = $(elStart).attr("targeturl");
          if (targeturl !== undefined && targeturl !== "") {
            $.post(targeturl, data, function (response) {
              // Sanity check
              if (response !== undefined) {
                if (response.status == "ok") {
                  if ('html' in response) {
                    $(elMsg).html(response['html']);
                    // Remove the contents after some time
                    setTimeout(function () { $(elMsg).html(""); }, 3000);
                  } else {
                    $(elMsg).html("Response is okay, but [html] is missing");
                  }
                } else {
                  $(elMsg).html("Could not interpret response " + response.status);
                }
              }
            });
          }

        } catch (ex) {
          private_methods.errMsg("simple_modify", ex);
        }
      },

      /**
       * simple_switch
       *    Switch in the simple search view
       *
       */
      simple_switch: function (elStart) {
        var elTargetType = "#id_targetType",
            elPos = "#id_searchpos",
            elLemma = "#id_searchlemma",
            elExc = "#id_searchexc",
            elRelated = "#related_constituents",
            elForms = "#id_simplerel-TOTAL_FORMS",
            sMoreLess = "",
            elMore = "#simple_more";

        try {
          sMoreLess = $(elStart).attr("mode");
          switch (sMoreLess) {
            case "more":
            case "less":
              // Check what we are up to
              if ($(".simple-search-2.hidden").length === 0) {
                // Nothing is hidden, so we are in extended search: return to simple search
                $(".simple-search-2").addClass("hidden");
                // Adapt the button to say we can turn to extended search
                $(elMore).attr("title", "Let me specify more");
                // Clear any extended search elements
                $(elPos).val("");
                $(elLemma).val("");
                $(elExc).val("");
                // Make sure the targettype is set correctly
                $(elTargetType).val("w");
                $(elMore).html("more");
                $(elMore).attr("mode", "more");
                // Remove all rows that are filled
                $(".rel-form").not(".empty-form").remove();
                $(elRelated).addClass("hidden");
                ru.cesar.seeker.show_related(false);

                // Also reset the number of forms
                $(elForms).val("0");

                // Modify the simple search at the server
                ru.cesar.seeker.simple_modify(elStart);

              } else {
                // We are in simple search: turn to extended search
                $(".simple-search-2").removeClass("hidden");
                // Adapt the button to say we can return to simple search
                $(elMore).attr("title", "Return to simple search");
                $(elMore).html("less");
                $(elMore).attr("mode", "less");
                // Show related button
                ru.cesar.seeker.show_related(true);
              }
              break;
          }
        } catch (ex) {
          private_methods.errMsg("simple_switch", ex);
        }
      },

      /**
       *  process_item
       *      Make a POST request to copy or delete an item
       *      Also show the waiting symbol by un-hiding a particular row
       *
       */
      process_item: function (el) {
        var elDiv = null,
            elNext = null,
            response = null,
            sUrl = "",
            frm = null,
            data = [];

        try {
          // Get to the nearest <div>
          elDiv = $(el).closest("div");
          // Get its second following sibling div
          elNext = $(elDiv).next(".part-process");
          if (elNext !== null) {
            //  We now have the correct row: open it
            $(elNext).removeClass("hidden");
            $(elDiv).addClass("hidden");
          }
          frm = $(el).closest("form");
          if (frm !== undefined) {
            data = $(frm).serializeArray();
            sUrl = $(el).attr("url");
            data.push({ 'name': 'caller', 'value': sUrl });
            // Anyway, start off an ajax call to request deletion
            response = ru.cesar.seeker.ajaxcall(sUrl, data, "POST");
            if (response !== undefined) {
              if (response.status === "ok") {
                // Continue through to the 'success' url
                sUrl = $(el).attr("success");
                window.location.href = sUrl;
              } else {
                // SOme kind of error was returned
                $(elNext).html(response.html);
              }
            }
          }
        } catch (ex) {
          private_methods.errMsg("process_item", ex);
        }
      },

      /**
       *  field_update
       *      Make a POST request to update a field
       *      Then post the returned message in the message ID
       */
      field_update: function (el, action) {
        var response=null,
            sUrl = "",
            frm = null,
            elMsg = null,
            data = [];

        try {
          elMsg = "#" + $(el).attr("msgid");
          if (action === undefined) { action = "save" };
          frm = $(el).closest("form");
          if (frm !== undefined) {
            // Prepare the data
            data = $(frm).serializeArray();
            // Get the correct URL
            sUrl = $(el).attr("ajaxurl");
            data.push({ 'name': 'action', 'value': action });
            // Post the data
            $.post(sUrl, data, function (response) {
              // Sanity check
              if (response !== undefined) {
                if (response.status == "ok") {
                  if ('html' in response) {
                    $(elMsg).html(response['html']);
                  } else {
                    $(elMsg).html("Response is okay, but [html] is missing");
                  }
                } else {
                  $(elMsg).html("Could not interpret response " + response.status);
                }
              }
            });
          }

        } catch (ex) {
          private_methods.errMsg("field_update", ex);
        }
      },

      /**
       * research_conditions
       *   Show the 'conditions' part and hide the remainder
       *
       */
      research_finetune(el) {
        try {
          // Hide the contents and show the tiles
          $("#research_tiles").addClass("hidden");
          $("#research_contents").addClass("hidden");
          $("#goto_overview").removeClass("hidden");
          $("#goto_finetune").addClass("hidden");
          $("#research_conditions").removeClass("hidden");
        } catch (ex) {
          private_methods.errMsg("research_conditions", ex);
        }
      },

      /**
       * research_open
       *   Open up a section and close another one
       *
       */
      research_open: function (sDivName, sDivClose, sBtnOpen, sBtnClose) {
        try {
          if (sDivName !== undefined && sDivName !== '') {
            $("#" + sDivName).removeClass("hidden");
          }
          // Possibly close [sDivClose]
          if (sDivClose !== undefined && sDivClose !== "") {
            $("#" + sDivClose).addClass("hidden");
          }
          // Possible open button
          if (sBtnOpen !== undefined && sBtnOpen !== '') {
            $("#" + sBtnOpen).removeClass("hidden");
          }
          // Possibly close [sBtnClose]
          if (sBtnClose !== undefined && sBtnClose !== "") {
            $("#" + sBtnClose).addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("research_open", ex);
        }
      },

      research_watch: function (elThis, sDivName, sDivClose) {
        var sDivProgress = "#research_progress",
            frm = null,
            data = [],
            ajaxurl = "",
            elStart = "#select_part",
            basket_id = "",
            part_id = "";

        try {
          // First open the correct places
          ru.cesar.seeker.research_open(sDivName, sDivClose);
          // Get all the needed values
          basket_id = $(elThis).attr("basket_id");
          part_id = $(elThis).attr("part_id");
          ajaxurl = $(elThis).attr("ajaxurl");
          // Then select the correct corpus in the list
          $(elStart).val(part_id);
          // Make the stop button available
          $("#research_stop").removeClass("hidden");
          // Disable the START button
          $("#research_start").prop("disabled", true);
          // Show what we are attempting
          $(sDivProgress).html("Attempting to catch the search...");

          // Gather the information
          frm = $(elStart).closest("form");
          if (frm !== undefined) { data = $(frm).serializeArray(); }

          // All went well -- get the basket information
          $.post(ajaxurl, data, function (response) {
            if (response !== undefined) {
              switch (response.status) {
                case "ok":
                  basket_id = response.basket_id;
                  basket_start = response.basket_start;
                  basket_progress = response.basket_progress;
                  basket_stop = response.basket_stop;
                  basket_watch = response.basket_watch;
                  basket_result = response.basket_result;
                  basket_data = data;
                  // Now start calling for status updates
                  setTimeout(function () { ru.cesar.seeker.search_progress(); }, 500);
                  break;
                default:
                  private_methods.errMsg("research_watch: incorrect response " + response.status);
                  break;
              }
            }
          });


        } catch (ex) {
          private_methods.errMsg("research_watch", ex);
        }
      },

      /**
       * research_overview
       *   Show the tiles-overview
       *
       */
      research_overview : function(el) {
        var sTargetUrl = "",
            bIsNew = false;

        try {
          // Check if this is a new one
          bIsNew = $(el).attr("isnew");
          if (typeof bIsNew !== typeof undefined && bIsNew !== false) {
            // Try get the target url
            sTargetUrl = $(el).attr("targeturl");
            // Open this page
            window.location.href = sTargetUrl;
          } else {
            // New code: just show all the relevant places and hide the others
            ru.cesar.seeker.main_show_hide({
              "research_tiles": true, "action_buttons": true, "edit_buttons": true,
              "exe_dashboard": false, "goto_overview": false, "goto_finetune": false,
              "research_conditions": false, "research_contents": false
            });
          }

        } catch (ex) {
          private_methods.errMsg("research_overview", ex);
        }
      },

      /**
       * main_show_hide
       *    Show/hide elements on the main panel
       *
       */
      main_show_hide(options) {
        var sDiv = "",
            bShow = true;
        try {
          for (var item in options) {
            if (options.hasOwnProperty(item)) {
              sDiv = "#" + item;
              bShow = options[item];
              if (bShow) {
                $(sDiv).removeClass("hidden");
              } else {
                $(sDiv).addClass("hidden");
              }
            }
          }
        } catch (ex) {
          private_methods.errMsg("main_show_hide", ex);
        }
      },
      
      /**
       * result_wizard
       *    Select one item from the result wizard
       *
       */
      result_wizard: function (el, sPart) {
        var sTargetId = "result_container_",
            sTargetType = "",
            sObjectId = "",
            sMsg = "",
            html = "",
            sAjaxMethod = "",
            sUrl = "",
            sBackId = "",
            data = {},
            frm = null,
            oTree = null,
            response = null,
            elListItem = null,
            elList = null;

        try {
          // Check for 'main'
          if (sPart !== undefined && sPart === "main") {
            // Do we have a targeturl?
            sUrl = $(el).attr("targeturl");
            if (sUrl === undefined || sUrl === false) {
              // THis means: return to the main center          
              $(".result-part").addClass("hidden");
              $(".result-part").removeClass("active");
              $("#goto_result_details").addClass("hidden");
              $("#action_buttons").removeClass("hidden");
              $("#result_info").removeClass("hidden");
              $("#result_host_containers").addClass("hidden");
              $("#result_filter_list").removeClass("hidden");
              $("#downloadcenter").removeClass("hidden");
            } else {
              // Go to this url
              window.location.href = sUrl;
            }
            
            return;
          }

          // Make sure we hide the jumbo buttons and the search result information
          $("#action_buttons").addClass("hidden");
          $("#result_info").addClass("hidden");
          $("#result_host_containers").removeClass("hidden");
          $("#result_wait_message").removeClass("hidden");
          $("#result_filter_list").addClass("hidden");
          $("#downloadcenter").addClass("hidden");

          frm = $("#qc_form");
          if (frm !== undefined) {
              data = $(frm).serializeArray();
              // Some items need data added
              switch (sPart) {
                case "1":
                  //  Make sure [result_hide_empty] is shown
                  $("#result_hide_empty").removeClass("hidden");
                  // Set the value properly
                  $("#hide_empty").val($("#hide_empty").prop("checked"));
                  // Make sure 'hide_empty' gets pushed
                  data.push({ 'name': 'hide_empty', 'value': $("#hide_empty").prop("checked") });
                  break;
                case "2":
                  // Patch for now
                  data.push({ 'name': 'qc', 'value': '1'});
                  break;
                case "4":
                case "5":
                case "6":
                  data.push({ 'name': 'resid', 'value': $(el).attr('resid') });
                  // Do we have a backid?
                  sBackId = $(el).attr("backid");
                  if (sBackId !== undefined && sBackId !== "") {
                    data.push({ 'name': 'backid', 'value': sBackId });
                  }
                  break;
              }
          }

          // Get the correct target id: a 'result_container_{num}'
          sTargetId = "#" + sTargetId + sPart;
          // Clear errors
          private_methods.errClear();
          // Get the correct id for this BASKET
          sObjectId = $("#basketid").text().trim();

          // [2] Load the new form through an AJAX call
          sAjaxMethod = "GET";
          var ajaxurl = $(el).attr("targeturl");
          switch (sPart) {
            case "2":
              sAjaxMethod = "POST";
            case "1":
            case "3":
            case "4":
            case "5":
            case "6":
              // CHeck if we need to take another instance id instead of #researchid
              if ($(el).attr("instanceid") !== undefined) { sObjectId = $(el).attr("instanceid"); }

              // POST call: show waiting
              $("#kwic-fetch").removeClass("hidden");
              // Fetch the correct data through a POST call
              response = ru.cesar.seeker.ajaxcall(ajaxurl, data, sAjaxMethod);
              if (response === undefined) {
                // serious business -- can't get answer from ajax call
                private_methods.errMsg("result_wizard: no response from ajax call");
              } else if ('status' in response) {
                switch (response.status) {
                  case "ok":
                    // Make the HTML response visible in a 'result_container_{num}'
                    $(sTargetId).html(response.html);
                    // Make sure events are set again
                    ru.cesar.seeker.init_events();
                    break;
                  case "error":
                    // Indicate there is an error
                    private_methods.errMsg("Response contains an error");
                    // Make the HTML response visible in a 'result_container_{num}'
                    $(sTargetId).html(response.html);
                    // Make sure events are set again
                    ru.cesar.seeker.init_events();
                    break;
                  default:
                    // Indicate there is an error
                    private_methods.errMsg("result_wizard: Unknown status: "+response.status);
                    break;
                }
              } else {
                // There is no status in the response
                private_methods.errMsg("result_wizard: no status in response from ajax call");
              }
              // POST call: hide waiting
              $("#kwic-fetch").addClass("hidden");
              break;
          }
          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);

          // Hide all research parts
          $(".result-part").not(sTargetId).addClass("hidden");
          $(".result-part").not(sTargetId).removeClass("active");

          // Show the target result part
          $(sTargetId).removeClass("hidden");

          // Show the 'back' button and hide ourselves
          switch (sPart) {
            case "1": case "2": case "3":
              $("#goto_result_details").removeClass("hidden");
              $("#goto_finetune").addClass("hidden");
              break;
            case "5":
              // Show the tree in the appropriate location
              oTree = JSON.parse( response.sent_info.allT);
              crpstudio.svg.treeToSvg("#sentdetails_tree", oTree, "#sentdetails_err");
              break;
            case "6":
              // Show the hierarchical table in the appropriate location
              oTree = JSON.parse(response.sent_info.allT);
              crpstudio.htable.treeToHtable("#sentdetails_htable", oTree, "#sentdetails_err");
              break;
          }
          $("#result_wait_message").addClass("hidden");


        } catch (ex) {
          private_methods.errMsg("result_wizard", ex);
        }
      },

      /**
       * treeToHtable
       *    Convert the object tree into a Htable
       *
       */
      treeToHtable: function (divHtable, oTree, divErr) {
        try {

        } catch (ex) {
          private_methods.errMsg("treeToHtable", ex);
        }
      },

      /**
       * research_wizard
       *    Select one item from the research project wizard
       *
       */
      research_wizard: function (el, sPart, bOnlyOpen, clstarget, sSelect) {
        var sTargetId = "research_container_",
            sContainerId = "research_container_",
            sTargetType = "",
            sObjectId = "",
            sMsg = "",
            html = "",
            sUrl = "",
            data = {},
            frm = null,
            th = null,
            response = null,
            elWait = null,      // Div that should be opened/closed to indicate waiting
            elListItem = null,
            elList = null;

        try {
          // Set waiting div
          elWait = private_methods.waitInit(el);
          // Start waiting
          private_methods.waitStart(elWait);

          // If this comes from the main dashboard, show waiting over there
          private_methods.mainWaitStart();
          
          // Get the correct target id
          if (clstarget !== undefined && clstarget !== "") {
            // Look for the nearest container
            sContainerId = "#" + $(el).closest(".research-part").first().attr("id");
            // Use [clstarget] for my own targetid: but only within the container
            sTargetId = sContainerId + " ." + clstarget;
          } else {
            sTargetId = "#" + sTargetId + sPart;
            sContainerId = sTargetId;
          }
          sObjectId = $("#researchid").text().trim();

          // Do we need to indicate selection?
          if (sSelect !== undefined && sSelect === "select") {
            // First deselect all <th> elements
            $(el).closest(".research-part").find("th").removeClass("selected");
            // Clear what we had
            $(sTargetId).html("");
            // Indicate that the <th> above is selected
            th = $(el).closest("th");
            if (th !== null) {
              $(th).addClass("selected");
            }
          }

          if (bOnlyOpen === undefined || bOnlyOpen === false) {
            sTargetType = $("#id_research-targetType").val();
            // If it is undefined, try to get the target type from the input
            if (sTargetType === undefined || sTargetType === "") {
              sTargetType = $("#targettype").text().trim();
              if (sTargetType === "") {
                sTargetType = "w";  // Take words as default
              }
            }
            // Before continuing: has the targettype been chosen?
            if (sPart !== "1") {
              // Sanity check          
              switch (sTargetType) {
                case "w":
                case "c":
                  private_methods.errClear();
                  break;
                default:
                  // There really is no other option, so warn the user and do not change place
                  private_methods.errMsg("Choose the main element type");
                  // Stop waiting
                  private_methods.waitStop(elWait);
                  // If this comes from the main dashboard, show waiting over there
                  private_methods.mainWaitStop();
                  // We need to LEAVE at this point
                  return;
              }
            }
            // Find the currently shown 'research-part' form
            frm = $(".research-part").not(".hidden").find("form");
            // [1] Some (increasingly many) calls require FIRST saving of the currently loaded information
            sMsg = "";
            switch (sPart) {
              case "42": sMsg = "4-before-42";
              case "43": if (sMsg === "") sMsg = "42-before-43";
              case "44": if (sMsg === "") sMsg = "43-before-44";
              case "62": if (sMsg === "") sMsg = "6-before-62";
              case "63": if (sMsg === "") sMsg = "62-before-63";
              case "72": if (sMsg === "") sMsg = "7-before-72";
              case "73": if (sMsg === "") sMsg = "72-before-73";
                // Opening a new form requires prior processing of the current form
                if (frm !== undefined) {
                  data = $(frm).serializeArray();
                  var button = $(frm).find(".submit-row .ajaxform");
                  if (button !== undefined) {
                    // Indicate we are saving
                    $(".save-warning").html("Processing... " + sMsg + loc_sWaiting);
                    data.push({ 'name': 'instanceid', 'value': $(button).attr("instanceid") });
                    // Determine the URL
                    sUrl = $(button).attr("ajaxurl");
                    // Process this information: save the data!
                    response = ru.cesar.seeker.ajaxcall(sUrl, data, "POST");
                    // Check the response
                    if (response.status === undefined || response.status !== "ok") {
                      // Action to undertake if we have not been successfull
                      private_methods.errMsg("research_wizard[" + sPart + "]: could not save the data for this function");
                      // Stop waiting
                      private_methods.waitStop(elWait);
                      // If this comes from the main dashboard, show waiting over there
                      private_methods.mainWaitStop();
                      // And leave...
                      return;
                    }
                  }
                }
                break;
            }
            switch (sPart) {
              case "62":
                // If a new condition has been created, then this is where we expect the instance number to appear
                if ('cond_instanceid' in response) {
                  $(el).attr("instanceid", response['cond_instanceid']);
                }
                break;
              case "72":
                // If a new feature has been created, then this is where we expect the instance number to appear
                if ('feat_instanceid' in response) {
                  $(el).attr("instanceid", response['feat_instanceid']);
                }
                break;
            }
          }

          // [2] Load the new form through an AJAX call
          data = [];
          switch (sPart) {
            case "1": case "2": case "3":
            case "4": case "42": case "43": case "44":
            case "6": case "62": case "63":
            case "7": case "72": case "73":
            case "8":

              // CHeck if we need to take another instance id instead of #researchid
              if ($(el).attr("instanceid") !== undefined) { sObjectId = $(el).attr("instanceid"); }
              // Indicate we are saving/preparing
              $(".save-warning").html("Processing... " + sPart + loc_sWaiting);
              // Determine the URL
              sUrl = $(el).attr("ajaxurl");
              if (sUrl === undefined) {
                sUrl = $(el).attr("targeturl");
              }
              // Fetch the corr
              response = ru.cesar.seeker.ajaxform_load(sUrl, sObjectId, data);
              if (response.status && response.status === "ok") {
                // Make the HTML response visible
                $(sTargetId).html(response.html);
                // Make sure events are set again
                ru.cesar.seeker.init_events();
                // Disable the save warning
                $(".save-warning").html("");
              }
              break;
          }
          // Bind the click event to all class="ajaxform" elements
          $(".ajaxform").unbind('click').click(ru.cesar.seeker.ajaxform_click);

          // Some actions depend on the particular page we are going to visit
          switch (sPart) {
            case "4": case "42":
              // add any event handlers for wizard part '42'
              ru.cesar.seeker.init_cvar_events();
              break;
            case "43": case "44":
            case "62": case "63":
            case "72": case "73":
            case "8": 
              // add any event handlers for wizard part '43' and part '44'
              // As well as for '62' and '63'
              ru.cesar.seeker.init_arg_events();
              break;
            case "6":
              // add any event handlers for wizard part '6'
              ru.cesar.seeker.init_cond_events();
              break;
            case "7":
              // add any event handlers for wizard part '7'
              ru.cesar.seeker.init_feat_events();
              break;
            case "5": // Page 5=Conditions

              // TODO: this still needs to be specified

              // Make sure the 'Type' field values are processed everywhere
              $(".cvar-item").each(function () {
                // Perform the same function as if we were clicking it
                ru.cesar.seeker.cvartype_click(this);
              });
              // Specify the change reaction function
              $(".cvar-type select").change(ru.cesar.seeker.cvartype_click);
              // Specify the function to be called when the user presses "summary"
              $(".func-summary").click(function () { ru.cesar.seeker.get_summary_click(this, "#cvar_summary"); });
              break;
          }
          // Hide all research parts
          $(".research-part").not(sTargetId).addClass("hidden");
          $(".research-part").not(sTargetId).removeClass("active");

          // $(sTargetId).removeClass("hidden");
          $(sContainerId).removeClass("hidden");
          // If this is not [Project Type] then get the project type
          if (sPart !== '1') {
            // Set the <input> element
            $("#research_part").val(sTargetType);
            // Hide all 
            $(".research-wrd").addClass("hidden");
            $(".research-cns").addClass("hidden");
            // Make sure everything of this target type is unhidden
            switch (sTargetType) {
              case "w": $(".research-wrd").removeClass("hidden"); break;
              case "c": $(".research-cns").removeClass("hidden"); break;
            }
          }
          // Determine what type we are
          // And then switch to the correct page
          switch ($(el).prop("tagName").toLowerCase()) {
            case "a":
              // Get the <li> element
              elListItem = $(el).parent();
              // Get the <ul> element
              elList = $(elListItem).parent();
              // Remove all actives
              $(elList).children("li.active").removeClass("active");
              $(elListItem).addClass("active");
              break;
            case "button":
              // Get the parent of the buttons
              elList = $(el).parent();
              // Adapt all the btn classes
              $(elList).children('button').each(function () {
                if ($(this).is(el)) {
                  $(this).addClass("btn-secondary");
                  $(this).removeClass("btn-primary");
                } else {
                  $(this).removeClass("btn-secondary");
                  $(this).addClass("btn-primary");
                }
              });
              break;
          }
          // Hide the tiles and show the contents
          $("#research_tiles").addClass("hidden");
          $("#research_contents").removeClass("hidden");
          $("#research_conditions").addClass("hidden");
          switch (sPart) {
            case "1": case "2": case "7":
              $("#goto_overview").removeClass("hidden");
              $("#goto_finetune").addClass("hidden");
              break;
            case "3": case "4": case "42": case "43":
            case "44": case "6":
              $("#goto_overview").removeClass("hidden");
              $("#goto_finetune").addClass("hidden");
              /* OLD code 
              $("#goto_overview").addClass("hidden");
              $("#goto_finetune").removeClass("hidden");
              */
              break;
          }
          // Stop waiting
          private_methods.waitStop(elWait);
          // If this comes from the main dashboard, show waiting over there
          private_methods.mainWaitStop();
        } catch (ex) {
          private_methods.errMsg("research_wizard", ex);
          // Stop waiting
          private_methods.waitStop(elWait);
        }
      },
      /**
      * main_info_hide
      *    Behaviour when there is a mouse-out on a main blob
      * 
      * @param {element} elRect
      * @returns {undefined}
      */
      main_info_hide: function (elRect) {
        try {
          $("#main_info_div").addClass("hidden");
        } catch (ex) {
          // Show the error at the indicated place
          private_methods.errMsg("main_info_hide error: ", ex);
        }
      },
      /**
      * main_info_show
      *    Behaviour when there is a mouse-over on a main blob
      * 
      * @param {element} elRect
      * @returns {undefined}
      */
      main_info_show: function (elRect) {
        var sPart,        // Counter
            i,            // Counter
            sInfoDiv = "#main_info_div",
            sInfo = "",
            lInfo = [],
            lHtml = [],   // Where we gather HTML
            oSvg,         // Coordinates of the svg rect element
            elTarget,     // The <div> we want to position
            oFeat = {},   // Feature object
            sId = "";     // Identifier of the element that has been hit

        try {
          // Validate: this must be a <g> element with class ".main-el"
          if (!$(elRect).is("g.main-el")) {
            return;
          }
          // The node must have an identifier
          sId = $(elRect).attr("id");
          // The text to be shown is in the @info attribute of the <g> element
          sInfo = $(elRect).attr("info");
          if (sInfo !== undefined && sInfo !== "") {
            // There is some text to be shown
            lInfo = sInfo.split("\\n");
            lHtml.push("<div id='info-" + sId + "' class='svg-main'><table>");
            for (i = 0; i < lInfo.length; i++) {
              sPart = lInfo[i];
              lHtml.push("<tr><td class='cellvalue'>" + sPart + "</td></tr>");
            }
            lHtml.push("</table></div>");

            // Add this element at an appropriate place
            $(sInfoDiv).html(lHtml.join("\n"));
            elTarget = $(sInfoDiv).find(".svg-main").get(0);

            // Get screen coordinates
            oSvg = private_methods.screenCoordsForRect($(elRect).children("rect").first());
            elTarget.style.left = oSvg['x'] + 'px';
            elTarget.style.top = (oSvg['y'] - 10 - 20 * lInfo.length).toString() + 'px';
            $(sInfoDiv).removeClass("hidden");

            /*
            // Now adjust the position based on the shown div
            oSvg = private_methods.fitFeatureBox(oSvg, elTarget);
            elTarget.style.left = oSvg['x'] + 'px';
            elTarget.style.top = oSvg['y'] + 'px';
            */
          }

        } catch (ex) {
          // Show the error at the indicated place
          private_methods.errMsg("main_info_show error: ", ex);
        }
      },

      /**
      * result_qsubinfo
      *    Open the following <tr> and KWIC-show [qsubinfo_id]
      * 
      * @param {element} elThis
      * @param {string} qsubinfo_id
      * @returns {void}
      */
      result_qsubinfo: function (elThis, qsubinfo_id) {
        var elTr = null,
            elWait = null,
            frm = null,
            data = null,
            ajaxurl = null,
            elTd = null;

        try {
          // Clear previous errors
          private_methods.errClear();
          // Set waiting div
          elWait = private_methods.waitInit(elThis);
          // Start waiting
          private_methods.waitStart(elWait);
          // Get the element we are looking for
          elTr = $(elThis).next("tr");
          // Are we opening or closing?
          if ($(elTr).hasClass("hidden")) {
            // We are trying to open and show
            // Hide all [.qsubinfo-show] items
            $(elThis).closest("tbody").find(".qsubinfo-show").addClass("hidden");
            // Show contents
            $(elTr).removeClass("hidden");
            elTd = $(elTr).children("td").first();
            $(elTd).html("<span><i>looking for the data...</i></span><span class=\"glyphicon glyphicon-refresh glyphicon-refresh-animate\"></span>");
            
            // Gather the information
            frm = $("#qc_form");
            if (frm !== undefined) { data = $(frm).serializeArray(); }

            // Ask for the required information
            ajaxurl = $(elThis).attr("ajaxurl");
            $.post(ajaxurl, data, function (response) {
              if (response.status === undefined) {
                // Show an error somewhere
                private_methods.errMsg("Bad qsubinfo response");
              } else if (response.status === "error") {
                // Show the error that has occurred
                if ("html" in response) { sMsg = response['html']; }
                if ("error_list" in response) { sMsg += response['error_list']; }
                private_methods.errMsg("Qsubinfo error: " + sMsg);
              } else {
                // Everything is in order: recover and show the data
                if ("html" in response) {
                  var sHtml = response["html"];
                  $(elTd).html(sHtml);
                }
              }
            });

          } else {
            // Need to close
            $(elTr).addClass("hidden");
          }

          // Stop waiting
          private_methods.waitStop(elWait);
        } catch (ex) {
          private_methods.errMsg("result_qsubinfo", ex);
          // Stop waiting
          private_methods.waitStop(elWait);
        }
      },
      /**
       * search_download
       *   Trigger creating and downloading the CRPX
       *
       */
      search_download: function (elStart) {
        var ajaxurl = "",
            response = null,
            basket_id = -1,
            frm = null,
            sMsg = "",
            data = [];

        try {
          // Clear the errors
          private_methods.errClear();

          // obligatory parameter: ajaxurl
          ajaxurl = $(elStart).attr("ajaxurl");

          // Gather the information
          frm = $(elStart).closest("form");
          // Set the 'action; attribute in the form
          frm.attr("action", ajaxurl);
          frm.submit();

        } catch (ex) {
          private_methods.errMsg("search_download", ex);
        }
      },

      /**
       * jumpto_item
       *   Jump to the indicated item
       *
       */
      jumpto_item: function (el) {
        var inst_type = "", // Instance type
            sPart = "",
            sUrl = "";      // URL to jump to

        try {
          if (el !== undefined) {
            inst_type = $(el).attr("jumptype");
            sUrl = $(el).attr("ajaxurl");
            if (inst_type !== undefined && inst_type !== "" && 
                sUrl !== undefined && sUrl !== "") {
              switch (inst_type) {
                case "cvar": sPart = "43"; break;
                case "cond": sPart = "62"; break;
                case "feat": sPart = "72"; break;
              }
              if (sPart !== "") {
                // Ask the wizard to open appropriately
                ru.cesar.seeker.research_wizard(el, sPart, true);
              }
            }
          }
        } catch (ex) {
          private_methods.errMsg("jumpto_item", ex);
        }
      },

      /**
       * result_download
       *   Trigger creating and downloading a result CSV
       *
       */
      post_download: function (elStart) {
        var ajaxurl = "",
            contentid = null,
            response = null,
            basket_id = -1,
            scaleFactor = 4,  // Scaling of images to make sure the result is not blurry
            frm = null,
            el = null,
            sHtml = "",
            oBack = null,
            dtype = "",
            resid="",
            sMsg = "",
            getCanvas,
            data = [];

        try {
          // Clear the errors
          private_methods.errClear();

          // obligatory parameter: ajaxurl
          ajaxurl = $(elStart).attr("ajaxurl");
          contentid = $(elStart).attr("contentid");

          // Gather the information
          frm = $(elStart).closest(".container-small").find("form");
          if (frm.length === 0) {
            frm = $(elStart).closest("td").find("form");
            if (frm.length === 0) {
              frm = $(elStart).closest(".container.body-content").find("form");
              if (frm.length === 0) {
                frm = $(elStart).closest(".container-large.body-content").find("form");
              }
            }
          }
          // Set the 'action; attribute in the form
          frm.attr("action", ajaxurl);
          // Make sure we do a POST
          frm.attr("method", "POST");

          // Get the download type and put it in the <input>
          dtype = $(elStart).attr("downloadtype");
          $(frm).find("#downloadtype").val(dtype);

          resid = $(elStart).attr("resid");
          if (resid !== undefined && resid != "") {
            $(frm).find("#resid").val(resid);
          }

          // Do we have a contentid?
          if (contentid !== undefined && contentid !== null && contentid !== "") {
            // Process download data
            switch (dtype) {
              case "tree":
                sHtml = private_methods.prepend_styles(contentid, "svg");
                // Set it
                $(frm).find("#downloaddata").val(sHtml);
                // Now submit the form
                oBack = frm.submit();
                break;
              case "htable":
                // Prepend any styles
                sHtml = private_methods.prepend_styles(contentid, "html");
                // Set it
                $(frm).find("#downloaddata").val(sHtml);
                // Now submit the form
                oBack = frm.submit();
                break;
              case "htable-png":
                // Make sure we get the table
                contentid = contentid + " table";
              case "tree-png":
                // Make sure we only get SVG
                if (dtype === "tree-png") {
                  // contentid = contentid + " svg";
                }
                // Convert html to canvas
                el = $(contentid).first().get(0);

                html2canvas(el, { scale: scaleFactor })
                  .then(function (canvas) {
                    // Convert to data
                    var imageData = canvas.toDataURL("image/png");
                    $(frm).find("#downloaddata").val(imageData);
                    // Now submit the form
                    oBack = frm.submit();
                });
                break;
              default:
                // TODO: add error message here
                return;
            }
          } else {
            // Do a plain submit of the form
            oBack = frm.submit();
          }

          // Check on what has been returned
          if (oBack !== null) {

          }
        } catch (ex) {
          private_methods.errMsg("post_download", ex);
        }
      },

      /**
       * rel_row_edit
       *   Start or finish editing of this row
       *
       */
      rel_row_edit: function (elStart, sAction, sSimpleName) {
        var elRow = null,
            elPos = null,
            elCat = null,
            targeturl = "",
            bSimpleName = (sSimpleName !== undefined && sSimpleName !== ""),
            elRelated = "#related_constituents",
            bNeedOpen = false;

        try {
          // Get to the row
          elRow = $(elStart).closest("tr");
          // Action switching
          switch (sAction) {
            case "open":    // Hide summary view and enter edit view
              // Is this closing simple naming?
              if (bSimpleName) {
                elRow = $(elStart).closest("table");
                $(elRow).find(".view-mode").addClass("hidden");
                $(elRow).find(".edit-mode").removeClass("hidden");
              } else {
                $(elRow).find(".rel-view-mode, .rel-edit-open").addClass("hidden");
                $(elRow).find(".rel-edit-mode, .rel-edit-close").removeClass("hidden");
                // Open up [.rel-cat] if it has a value
                elCat = $(elRow).find(".rel-cat input").first();
                if ($(elCat).val() !== "") { $(elRow).find(".rel-cat").removeClass("hidden"); }
                // Open up [.rel-pos] if it has a value
                $(elRow).find(".rel-pos select").each(function (idx, el) {
                  if ($(el).val() !== "") { bNeedOpen = true; }
                });
                if (bNeedOpen) { $(elRow).find(".rel-pos").removeClass("hidden"); }
              }
              break;
            case "close":   // Hide edit view and enter summary view
              // Is this closing simple naming?
              if (bSimpleName) {
                // Test if a name has been provided
                if ($("#id_baresimple").val() === "") {
                  // No name provided: open simple view
                  targeturl = $(elRow).attr("targeturl");
                  window.location.href = targeturl;
                } else {
                  // A name has been provided: close this view
                  $(".tablefield.simple-search-named .view-mode").each(function (k, el) {
                    var elTd = $(el).closest("td"),
                        value = "";

                    // Get the value
                    if ($(elTd).find("input").length > 0) {
                      value = $(elTd).find("input").first().val();
                    } else if ($(elTd).find("textarea").length > 0) {
                      value = $(elTd).find("textarea").first().val();
                    }
                    // Set the value
                    $(elTd).find(".view-mode").first().html(value);
                  });
                  $(".simple-search-named .edit-mode").addClass("hidden");
                  $(".simple-search-named .view-mode").removeClass("hidden");
                  // Make sure the button fits
                  $("#save_as").html("Save");
                }
              } else {
                // Main stuff: Check if all is well
                if (ru.cesar.seeker.related_view(elRelated)) {
                  $(elRow).find(".rel-view-mode, .rel-edit-open").removeClass("hidden");
                  $(elRow).find(".rel-edit-mode, .rel-edit-close").addClass("hidden");
                  $(elRow).find(".rel-cat, .rel-pos").addClass("hidden");
                  // No errors
                  $(elRow).find(".rel-name-err").addClass("hidden");
                  // Updated related
                  ru.cesar.seeker.simple_update();
                } else {
                  // SIgnal that the name should be specified
                  $(elRow).find(".rel-name-err").removeClass("hidden");
                  $(elRow).find(".rel-name-err").html(loc_sRelatedErr);
                }
              }
              break;
          }

        } catch (ex) {
          private_methods.errMsg("rel_row_edit", ex);
        }
      },

      /**
       * rel_row_extra
       *   Start or finish editing of extra information in [sClass]
       *
       */
      rel_row_extra: function (elStart, sClass) {
        var elRow = null,
            elTbody = null,
            elItem = null,
            bVisible = false;

        try {
          // Get to the row
          elRow = $(elStart).closest("tr");
          elTbody = $(elStart).closest("tbody");
          // CHeck if the class is visible
          elItem = $(elTbody).find("." + sClass).first();
          if (elItem === null) { return; }
          bVisible =  (! $(elItem).hasClass("hidden"));
          // Action depends on the class
          switch (sClass) {
            case "rel-cat":
            case "rel-text":
            case "rel-lemma":
              if (bVisible) {
                // Need to make it invisible and clear the contents
                $(elItem).addClass("hidden");
                $(elItem).find("input").val("");
              } else {
                // Need to make sure it is shown
                $(elItem).removeClass("hidden");
              }
              break;
            case "rel-pos":
              if (bVisible) {
                // Need to make it invisible and clear the contents
                $(elItem).addClass("hidden");
                $(elItem).find("select").val("");
              } else {
                // Need to make sure it is shown
                $(elItem).removeClass("hidden");
              }
              break;
          }

        } catch (ex) {
          private_methods.errMsg("rel_row_extra", ex);
        }
      },

      /**
       * search_start
       *   Check and then start a search
       *
       *   Note: returning from the $.post call only means
       *         that a BASKET object has been created...
       *   Note 2: this function can also be called from SIMPLE search.
       *
       */
      search_start: function(elStart, after_finish) {
        var sDivProgress = "#research_progress",
            ajaxurl = "",
            butWatch = null,  // The button that contains the in progress
            response = null,
            basket_id = -1,
            frm = null,
            bChecked = false,
            i = 0,
            sMsg = "",
            sWord = "",         // For simple search
            sLemma = "",        // For simple search
            sCat = "",          // For simple search
            sExc = "",          // For simple search
            sFcat = "",         // For simple search
            sFval = "",         // For simple search
            sCql = "",          // For extended search
            sTargetType = "",   // For simple search
            data = [];

        try {
          // Clear the errors
          private_methods.errClear();

          // obligatory parameter: ajaxurl
          ajaxurl = $(elStart).attr("ajaxurl");

          // Gather the information
          frm = $(elStart).closest("form");
          if (frm !== undefined) { data = $(frm).serializeArray(); }

          // Check if this is simple search
          if (private_methods.is_in_list(data, "is_simple_search")) {
            // Get the word, lemma, category
            sWord = private_methods.get_list_value(data, "searchwords");
            sLemma = private_methods.get_list_value(data, "searchlemma");
            sCat = private_methods.get_list_value(data, "searchpos");
            sFcat = private_methods.get_list_value(data, "searchfcat");
            sFval = private_methods.get_list_value(data, "searchfval");
            sExc = private_methods.get_list_value(data, "searchexc");
            sCql = private_methods.get_list_value(data, "searchcql");
            // Determine the targetType
            sTargetType = "e";
            if (sCql !== "") {sTargetType = "q"; }
            else if (sWord !== "" && sLemma === "" && sFval === "" && sCat === "") { sTargetType = "w"; }
            else if (sWord === "" && sLemma === "" && sFval === "" && sCat !== "") { sTargetType = "c";}
            // Set the targetType
            $("#id_targetType").val(sTargetType);
            // Change the value in the list
            private_methods.set_list_value(data, "targetType", sTargetType);
            // pass on the list of possible 'towards' names
            if (loc_towards.length === 0) {
              // Double check this list
              bChecked = true;
              $("#related_constituents tr.rel-form").not(".empty-form").find("td.rel-name input").each(function (k, el) {
                loc_towards.push($(el).val());
              });
            }
            data.push({"name": "ltowards", "value": JSON.stringify(loc_towards)});
            // Double check this list
            bChecked = true;
            $("#related_constituents tr.rel-form").not(".empty-form").find("td.rel-name input").each(function (k, el) {
              var relName = $(el).val();
              // Check this name too
              if (relName === undefined || relName === "") {
                bChecked = false;
                $(el).attr("placeholder","a NAME is needed");
              }
            });
            if (!bChecked) {
              // SOrry, but we cannot continue
              return;
            }
          }

          // Start the search
          $(sDivProgress).html("Contacting the search server")

          // Hide some buttons
          $("#research_stop").addClass("hidden");
          $("#research_results").addClass("hidden");

          // Make an ASYNCHRONOUS ajax call to START OFF the search
          $.post(ajaxurl, data, function (response) {
            var lHtml = [];

            if (response.status === undefined) {
              // Show an error somewhere
              private_methods.errMsg("Bad execute response");
              $(sDivProgress).html("Bad execute response:<br>" + response);
            } else if (response.status === "error") {
              // Show the error that has occurred
              if ("html" in response) { sMsg = response['html']; }
              if ("error_list" in response && response['error_list'] !== "") {
                // Don't really use this:
                sMsg += response['error_list'];
                // Experimental: only show this error list
                lHtml.push("<span style=\"color: darkred;\">");
                lHtml.push(response['error_list']);
                lHtml.push("</span>");
                $(sDivProgress).html(lHtml.join("\n"));
              } else {
                private_methods.errMsg("Execute error: " + sMsg);
                $(sDivProgress).html("execution error");
              }
            } else {
              // All went well -- get the basket id
              basket_id = response.basket_id;
              basket_start = response.basket_start;
              basket_progress = response.basket_progress;
              basket_stop = response.basket_stop;
              basket_watch = response.basket_watch;
              basket_result = response.basket_result;
              basket_data = data;

              // Make the watch (=InProgress) button available
              butWatch = $("#action_inprogress").find("button").first();
              $(butWatch).attr("ajaxurl", basket_watch);
              $(butWatch).attr("basket_id", basket_id);
              $(butWatch).attr("part_id", $("#select_part").val());
              $("#action_inprogress").removeClass("hidden");

              // Make the stop button available
              $("#research_stop").removeClass("hidden");
              $(sDivProgress).html("Conversion to Xquery...");
              // Disable the START button
              $("#research_start").prop("disabled", true);

              // Start the next call for status after 2 seconds
              setTimeout(function () { ru.cesar.seeker.search_progress(after_finish); }, 500);

              // Now make sure that the Translation + Execution starts
              $.post(basket_start, data, function (response) {
                // Interpret the response that is returned
                if (response.status === undefined) {
                  // Show an error somewhere
                  private_methods.errMsg("Basket-start response status undefined");
                  $(sDivProgress).html("Bad execute response:<br>" + response);
                  $("#action_inprogress").addClass("hidden");
                } else if (response.status === "error") {
                  // Immediately set the 'internal' error
                  loc_bExeErr = true;
                  // Show the error that has occurred
                  if ("html" in response) { sMsg = response['html']; }
                  if ("error_list" in response) { sMsg += response['error_list']; }
                  // Show that the project has finished
                  if ("html" in response) {
                    $(sDivProgress).html(response.html);
                  } else {
                    private_methods.errMsg("Execute error: " + sMsg);
                    $(sDivProgress).html("execution error (see above)");
                  }
                  $("#action_inprogress").addClass("hidden");
                  // Hide the stop button, because we have already stopped
                  $("#research_stop").addClass("hidden");
                } else {
                  // All went well, and the search has finished
                  // No further action is needed unless after_finish is defined
                }
                // Re-enable the START button in all cases
                $("#research_start").prop("disabled", false);
              });
            }
          });

        } catch (ex) {
          private_methods.errMsg("search_start", ex);
        }
      },

      /**
       *  save_as_advanced
       *
       */
      save_as_advanced: function () {
        try {
          $("#save_as_advanced").removeClass("hidden");
        } catch (ex) {
          private_methods.errMsg("save_as_advanced", ex);
        }
      },

      /**
       * simple_save
       *   Save a simple search
       *
       */
      simple_save: function (elStart, savetype) {
        var sDivProgress = "#research_progress",
            sDivBare = "#baresimple_result",
            sDivName = "#search_simple_name",
            sDivBareName = "#id_baresimple",
            sSimpleType = "project",
            elDetails = "#tabsimpledetails",
            ajaxurl = "",
            response = null,
            frm = null,
            sSaveName = "",
            sUrl = "",
            sMsg = "",
            lHtml = [],
            data = [];

        try {
          // Clear the errors
          private_methods.errClear();

          // Double check
          if ($(elDetails).hasClass("hidden")) {
            $(elDetails).removeClass("hidden");
            return;
          }

          // obligatory parameter: ajaxurl
          ajaxurl = $(elStart).attr("ajaxurl");

          // Gather the information
          frm = $(elStart).closest("form");
          if (frm !== undefined) { data = $(frm).serializeArray(); }

          if (savetype == undefined) { savetype = "project"; }
          switch (savetype) {
            case "bare":
              // Check if there is a name specified
              if ($(sDivBareName).val() === "") {
                // No name specified yet: show the Save parameters
                $(".simple-view-details .edit-mode").removeClass("hidden");
                $(".simple-view-details .view-mode").addClass("hidden");
                $(".simple-view-details .simple-search-named").removeClass("hidden");
                $(".simple-view-details").removeClass("hidden");
                return;
              }

              sDivProgress = "#baresimple_result";
              sSimpleType = "simple search";
              // pass on the list of possible 'towards' names
              if (loc_towards.length === 0) {
                // Double check this list
                bChecked = true;
                $("#related_constituents tr.rel-form").not(".empty-form").find("td.rel-name input").each(function (k, el) {
                  loc_towards.push($(el).val());
                });
              }
              data.push({ "name": "ltowards", "value": JSON.stringify(loc_towards) });
              // Prepare what we see
              $(sDivProgress).parent().find(".pre-save").removeClass("hidden");
              $(sDivProgress).parent().find(".post-save").html("");
              $(sDivProgress).parent().find(".post-save").removeClass("hidden");
              break;
            default:
              sDivProgress = "#research_progress";
              sSimpleType = "project";
              break;
          }

          // Make a call to the ajaxurl
          $.post(ajaxurl, data, function (response) {
            if (response.status === undefined) {
              // Show an error somewhere
              private_methods.errMsg("Bad execute response");
              $(sDivProgress).html("Bad execute response:<br>" + response);
            } else if (response.status === "error") {
              // Show the error that has occurred
              if ("html" in response) { sMsg = response['html']; }
              if ("error_list" in response && response['error_list'] !== "") {
                // Don't really use this:
                sMsg += response['error_list'];
                // Experimental: only show this error list
                lHtml.push("<span style=\"color: darkred;\">");
                lHtml.push(response['error_list']);
                lHtml.push("</span>");
                $(sDivProgress).html(lHtml.join("\n"));
              } else {
                private_methods.errMsg("Execute error: " + sMsg);
                $(sDivProgress).html("execution error");
              }
            } else {
              // Everything went well
              sSaveName = response['name'];
              sUrl = response['editurl'];
              // Create a response
              lHtml.push("<div>");
              lHtml.push("<p>Open project <span class='badge'>" + sSaveName + "</span> here below</p>");
              lHtml.push("<p>");
              switch (savetype) {
                case "project":
                  lHtml.push("<a type='button' title='open the new project' class='btn btn-success btn-xs'");
                  lHtml.push(" href=\"" + sUrl + "\">");
                  lHtml.push(" <span class='glyphicon glyphicon-folder-open' aria-hidden='true'></span>");
                  lHtml.push("</a>");
                  lHtml.push("</p>");
                  break;
                case "bare":
                  // Make sure the name gets displayed properly
                  $(sDivName).html(sSaveName);
                  $(sDivName).addClass("badge");
                  // Check if we have the VIEW
                  if ("view" in response) {
                    window.location.href = response['view'];
                  }
                  break;
              }
              lHtml.push("</div>");
              // Show the responses
              $(sDivProgress).html(lHtml.join("\n"));
              $(sDivProgress).parent().find(".pre-save").addClass("hidden");

              // Make sure the .simple-view-details is shown correctly

            }
          });

        } catch (ex) {
          private_methods.errMsg("simple_save", ex);
        }
      },
      
      /**
       * search_stop
       *   Stop an already going search
       *
       */
      search_stop : function(el) {
        var sDivProgress = "#research_progress",
            response = null;
        try {
          // Enable the START button
          $("#research_start").prop("disabled", false);
          // Hide the in progress button
          $("#action_inprogress").addClass("hidden");
          // Make an AJAX call by using the already stored basket_stop URL
          $.post(basket_stop, basket_data, function (response) {
            if (response.status !== undefined) {
              switch (response.status) {
                case "ok":
                  $(sDivProgress).html("Stopped gracefully");
                  break;
                case "error":
                  $(sDivProgress).html("Stopped with an error");
                  break;
              }
            }
          });

        } catch (ex) {
          private_methods.errMsg("search_stop", ex);
        }
      },

      /**
       * search_progress
       *   Elicit and show the status of an ongoing search
       *
       */
      search_progress(after_finish) {
        var sDivProgress = "#research_progress",
            response = null,
            html = [],
            sMsg = "";

        try {
          // First of all check for internal error
          if (loc_bExeErr) return;
          // Make an AJAX call by using the already stored basket_stop URL
          // response = ru.cesar.seeker.ajaxcall(basket_progress, basket_data, "POST");
          $.post(basket_progress, basket_data, function (response) {
            if (response.status !== undefined) {
              if ('html' in response) { sMsg = response.html; }
              switch (response.status) {
                case "ok":
                  // Action depends on the statuscode
                  switch (response.statuscode) {
                    case "working":
                    case "preparing":
                      // Prevent error progression
                      if (loc_bExeErr) return;
                      // Show the status of the project
                      $(sDivProgress).html(response.html);
                      // Make sure we are called again
                      setTimeout(function () { ru.cesar.seeker.search_progress(after_finish); }, 500);
                      break;
                    case "completed":
                      // Prevent error progression
                      if (loc_bExeErr) return;
                      // Show that the project has finished
                      $(sDivProgress).html(response.html);
                      // Hide the STOP button
                      $("#research_stop").addClass("hidden");
                      // Allow starting again
                      $("#research_start").prop("disabled", false);
                      // Show the RESULTS button
                      $("#research_results").removeClass("hidden");
                      // Set the correct href for the button
                      $("#research_results").attr("href", basket_result);
                      // Hide the IN-PROGRESS button
                      $("#action_inprogress").addClass("hidden");
                      if (after_finish !== undefined) {
                        after_finish();
                      }
                      break;
                    case "error":
                      // THis is an Xquery error
                      // Show that the project has finished
                      $(sDivProgress).html("Sorry, but there is an error");
                      // Hide the STOP button
                      $("#research_stop").addClass("hidden");
                      // Do NOT shoe the RESULTS button
                      // Hide the IN-PROGRESS button
                      $("#action_inprogress").addClass("hidden");
                      break;
                    case "stop":
                      // Stop asking for progress
                      // Hide the STOP button
                      $("#research_stop").addClass("hidden");
                      // Hide the IN-PROGRESS button
                      $("#action_inprogress").addClass("hidden");
                      break;
                    default:
                      // Prevent error progression
                      if (loc_bExeErr) return;
                      // Now look at the status code
                      if (response.statuscode !== "") {
                        // Show the current status
                        private_methods.errMsg("Unknown statuscode: [" + response.statuscode + "]");
                      }
                      // We continue anyway, because this is not an error
                      setTimeout(function () { ru.cesar.seeker.search_progress(after_finish); }, 500);
                      break;
                  }
                  break;
                case "error":
                  if ('error_list' in response) { sMsg += response.error_list; }
                  private_methods.errMsg("Progress error: " + sMsg);
                  // Hide the IN-PROGRESS button
                  $("#action_inprogress").addClass("hidden");
                  break;
                case "stop":
                  // Hide the IN-PROGRESS button
                  $("#action_inprogress").addClass("hidden");
                  // No further action is needed unless there is a message??
                  break;
              }
            }
          });

        } catch (ex) {
          private_methods.errMsg("search_progress", ex);
        }
      },

      /**
       * select_qc
       *   Set the 'qc' to the correct div and then open [sDivOpen]
       *
       */
      select_qc: function (elThis, sDivQc, sDivOpen) {
        try {
          var iSelectedQc = parseInt($(elThis).val(), 10);
          $("#"+sDivQc).html(str(iSelectedQc));
          $("#" + sDivOpen).removeClass("hidden");
        } catch (ex) {
          private_methods.errMsg("select_qc", ex);
        }
      },

      /**
       * sent_click
       *   Show waiting symbol when sentence is clicked
       *
       */
      sent_click: function () {
        $("#sentence-fetch").removeClass("hidden");
      },

      /**
       * tabular_deleterow
       *   Delete one row from a tabular inline
       *
       */
      tabular_deleterow: function () {
        var sId = "",
            elRow = null,
            elForms = "#id_simplerel-TOTAL_FORMS",
            iForms = 0,
            prefix = "simplerel",
            bValidated = false;

        try {
          // Find out just where we are
          sId = $(this).closest("div").attr("id");
          // Find out how many forms there are right now
          iForms = $(elForms).val();
          // The validation action depends on this id
          switch (sId) {
            case "search_mode_simple":
              // TODO: add proper validation
              bValidated = true;
              break;
          }
          // Continue with deletion only if validated
          if (bValidated) {
            // Get to the row
            elRow = $(this).closest("tr");
            $(elRow).remove();
            // Decrease the amount of forms
            iForms -= 1;
            $(elForms).val(iForms);

            // Re-do the numbering of the forms that are shown
            $(".rel-form").not(".empty-form").each(function (idx, elThisRow) {
              var iCounter = 0, sRowId = "", arRowId = [];

              iCounter = idx + 1;
              // Adapt the ID attribute -- if it EXISTS
              sRowId = $(elThisRow).attr("id");
              if (sRowId !== undefined) {
                arRowId = sRowId.split("-");
                arRowId[1] = idx;
                sRowId = arRowId.join("-");
                $(elThisRow).attr("id", sRowId);
              }

              // Adjust the number in the FIRST <td>
              $(elThisRow).find("td").first().html(iCounter.toString());

              // Adjust the numbering of the INPUT and SELECT in this row
              $(elThisRow).find("input, select").each(function (j, elInput) {
                // Adapt the name of this input
                var sName = $(elInput).attr("name");
                var arName = sName.split("-");
                arName[1] = idx;
                sName = arName.join("-");
                $(elInput).attr("name", sName);
                $(elInput).attr("id", "id_" + sName);
              });
            });

            // The validation action depends on this id
            switch (sId) {
              case "search_mode_simple":
                // Update
                ru.cesar.seeker.simple_update();
                break;
            }
          }

        } catch (ex) {
          private_methods.errMsg("tabular_deleterow", ex);
        }
      },

      /**
       * tabular_addrow
       *   Add one row into a tabular inline
       *
       */
      tabular_addrow: function () {
        //var arTable = ['research_intro-wrd', 'research_intro-cns', 'research_gvar', 'research_vardef', 'research_spec', 'research_cond'],
        //    arPrefix = ['construction', 'construction', 'gvar', 'vardef', 'function', 'cond'],
        //    arNumber = [true, true, false, false, false, true],
        var arTdef = lAddTableRow,
            oTdef = {},
            rowNew = null,
            elTable = null,
            iNum = 0,     // Number of <tr class=form-row> (excluding the empty form)
            sId = "",
            i;

        try {
          // Find out just where we are
          sId = $(this).closest("div").attr("id");
          // Walk all tables
          for (i = 0; i < arTdef.length; i++) {
            // Get the definition
            oTdef = arTdef[i];
            if (sId === oTdef.table || sId.indexOf(oTdef.table) >= 0) {
              // Go to the <tbody> and find the last form-row
              elTable = $(this).closest("tbody").children("tr.form-row.empty-form")

              // Perform the cloneMore function to this <tr>
              rowNew = ru.cesar.seeker.cloneMore(elTable, oTdef.prefix, oTdef.counter);
              // Call the event initialisation again
              if (oTdef.events !== null) {
                oTdef.events();
              }
              // Any follow-up activity
              if ('follow' in oTdef && oTdef['follow'] !== null) {
                oTdef.follow(rowNew);
              }
              // We are done...
              break;
            }
          }
        } catch (ex) {
          private_methods.errMsg("tabular_addrow", ex);
        }
      },

      /**
       * task_save
       *   Perform the SAVE function with an additional task
       *
       */
      task_save: function (sTask, elThis, function_id) {
        var divTarget = null, // The select function
            divSave = null;   // THe save button

        try {
          divTarget = $(elThis).parent().find("select").first();
          if (sTask !== undefined && function_id !== undefined && divTarget !== null) {
            // Prepare data
            var data = []
            data.push({ 'name': '_task', 'value': sTask });
            switch (sTask) {
              case "copy_cvar_function":
                data.push({ 'name': '_functionid', 'value': function_id });
                data.push({ 'name': '_constructionid', 'value': $(divTarget).val() });
                break;
              case "copy_condition_function":
                data.push({ 'name': '_functionid', 'value': function_id });
                data.push({ 'name': '_conditionid', 'value': $(divTarget).val() });
                break;
              case "copy_feature_function":
                data.push({ 'name': '_functionid', 'value': function_id });
                data.push({ 'name': '_featureid', 'value': $(divTarget).val() });
                break;
            }
            // Find out where the save button is located
            divSave = $(elThis).closest("form").find(".submit-row button").first();
            if (divSave !== null) {
              // Position the data in place
              $(divSave).attr("extra", JSON.stringify( data));
              // Simulate pressing the 'SAVE' button with these data
              ru.cesar.seeker.ajaxform_click.call(divSave);
            }
          }
        } catch (ex) {
          private_methods.errMsg("task_save", ex);
        }
      },

      /**
       *  toggle_del
       *      Toggle research item
       *
       */
      toggle_del: function (el) {
        var elTr = null;

        try {
          // Get to the nearest <tr>
          elTr = $(el).closest("tr");
          // Is this .part-del?
          if ($(elTr).is(".part-del")) {
            // Hide it
            $(elTr).addClass("hidden");
          } else {
            // Get to the next .part-del
            elTr = $(elTr).nextAll(".part-del").first();
            // Show it
            $(elTr).removeClass("hidden");
            // Also make sure the correct contents is shown
            $(elTr).find(".part-del").removeClass("hidden");
            $(elTr).find(".part-process").addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("toggle_del", ex);
        }
      },

      /**
       * load_form
       *   Clicking an ADD button leads to this function to load a new form
       *
       */
      load_form: function (elThis, additional) {
        var elGroup = null,
            elTarget = null,
            targeturl = "",
            sStatus = "";

        try {
          // Get the target to be opened
          elTarget = $(elThis).attr("targetid");
          targeturl = $(elThis).attr("targeturl");
          // Sanity check
          if (elTarget !== null && targeturl !== "") {
            // Show it if needed
            if ($("#" + elTarget).hasClass("hidden")) {
              // Load a form
              $.get(targeturl, function (response) {
                if (response !== undefined && response !== "" && 'status' in response) {
                  switch (response['status']) {
                    case "ok":
                      $("#"+elTarget).html(response['html']);
                      break;
                    default:
                      break;
                  }
                }
                // Show the form
                $("#" + elTarget).removeClass("hidden");
                // If there is an additional requirement, then fulfill it
                if (additional !== undefined) {
                  switch (additional) {
                    case "nextrow": // Show the next <tr>
                      $(elThis).closest("tr").next("tr").removeClass("hidden");
                      break;
                  }
                }
                // Make sure events are active again
                ru.cesar.seeker.init_events();
              });

            } else {
              $("#" + elTarget).addClass("hidden");
              // If there is an additional requirement, then fulfill it
              if (additional !== undefined) {
                switch (additional) {
                  case "nextrow": // Show the next <tr>
                    $(elThis).closest("tr").next("tr").addClass("hidden");
                    break;
                }
              }
            }
          }
        } catch (ex) {
          private_methods.errMsg("load_form", ex);
        }
      },

      /**
       * toggle_click
       *   Action when user clicks an element that requires toggling a target
       *
       */
      toggle_click: function (elThis, class_to_close, class_to_open) {
        var elGroup = null,
            elTarget = null,
            sStatus = "";

        try {
          // Get the target to be opened
          elTarget = $(elThis).attr("targetid");
          // Sanity check
          if (elTarget !== null) {
            // Show it if needed
            if ($("#"+elTarget).hasClass("hidden")) {
              $("#" + elTarget).removeClass("hidden");
              if (class_to_open !== undefined && class_to_open !== "") {
                $("." + class_to_open).addClass("hidden");
              }
            } else {
              $("#" + elTarget).addClass("hidden");
              // Check if there is an additional class to close
              if (class_to_close !== undefined && class_to_close !== "") {
                $("." + class_to_close).addClass("hidden");
              }
              if (class_to_open !== undefined && class_to_open !== "") {
                $("." + class_to_open).removeClass("hidden");
              }
            }
          }
        } catch (ex) {
          private_methods.errMsg("toggle_click", ex);
        }
      },

      /**
       * toggle_simple_save
       *   Action when user clicks the 'save' button to show/hide the simple save information
       *
       */
      toggle_simple_save: function (elThis, class_to_close, class_to_open) {
        var elGroup = null,
            elTarget = null,
            sStatus = "";

        try {
          // Get the target to be opened
          elTarget = $(elThis).attr("targetid");
          // Sanity check
          if (elTarget !== null) {
            // Show it if needed
            if ($("#" + elTarget).hasClass("hidden")) {
              $("#" + elTarget).removeClass("hidden");
              if (class_to_open !== undefined && class_to_open !== "") {
                $("." + class_to_open).addClass("hidden");
              }
            } else {
              $("#" + elTarget).addClass("hidden");
              // Check if there is an additional class to close
              if (class_to_close !== undefined && class_to_close !== "") {
                $("." + class_to_close).addClass("hidden");
              }
              if (class_to_open !== undefined && class_to_open !== "") {
                $("." + class_to_open).removeClass("hidden");
              }
            }
          }
        } catch (ex) {
          private_methods.errMsg("toggle_simple_save", ex);
        }
      },

      /**
       * toggle_prjview
       *   Showing or hiding non-recent projects
       *
       */
      toggle_prjview: function (elThis) {
        try {
          if ($(elThis).html().indexOf("more") === 0) {
            // Change the text
            $(elThis).html("less...");
            // Show all nonrecent projects
            $(".nonrecent").removeClass("hidden");
          } else {
            // Change the text
            $(elThis).html("more...");
            // Hide all nonrecent projects
            $(".nonrecent").addClass("hidden");
          }

        } catch (ex) {
          private_methods.errMsg("toggle_prjview", ex);
        }
      },

      /**
       * toggle_textarea_click
       *   Action when user clicks [textarea] element
       *
       */
      toggle_textarea_click: function () {
        var elGroup = null,
            elSpan = null,
            sStatus = "";

        try {
          // Get the following <span> of class td-textarea
          elSpan = $(this).next(".td-textarea");
          // Sanity check
          if (elSpan !== null) {
            // Show it if needed
            if ($(elSpan).hasClass("hidden")) {
              $(elSpan).removeClass("hidden");
            }
            // Hide myself
            $(this).addClass("hidden");
          }
        } catch (ex) {
          private_methods.errMsg("toggle_textarea_click", ex);
        }
      },

      /**
       * toggle_textarea_out
       *   Action when mouse leaves [textarea] element
       *
       */
      toggle_textarea_out: function () {
        var elSpan = null,
            sText = "";

        try {
          // Get the text inside the textarea
          sText = $(this).children().first().html();
          if ($.trim(sText) !== "") {
            // Get the previous <span> of class td-toggle-textarea
            elSpan = $(this).prev(".td-toggle-textarea");
            // Check
            if (elSpan !== null) {
              // Hide the textarea and show the text
              $(elSpan).children().first().html(sText);
              $(elSpan).removeClass("hidden");
              $(this).addClass("hidden");
            }
          }
        } catch (ex) {
          private_methods.errMsg("toggle_textarea_out", ex);
        }
      },

      /**
       * process_edit
       *   Switch between edit modes on this <tr>
       *   And if saving is required, then call the [targeturl] to send a POST of the form data
       *
       */
      process_edit: function (el, sType, oParams) {
        var //el = this,
            sMode = "",
            colspan = "",
            targeturl = "",
            targetid = "",
            afterurl = "",
            targethead = null,
            lHtml = [],
            data = null,
            key = "",
            i = 0,
            frm = null,
            bOkay = true,
            bReloading = false,
            manutype = "",
            err = "#little_err_msg",
            elTr = null,
            elView = null,
            elEdit = null;

        try {
          // Possibly correct [el]
          if (el !== undefined && "currentTarget" in el) { el = el.currentTarget; }
          // Get the mode
          if (sType !== undefined && sType !== "") {
            sMode = sType;
          } else {
            sMode = $(el).attr("mode");
          }
          // Get the <tr>
          elTr = $(el).closest("td");
          // Get the manutype
          manutype = $(el).attr("manutype");
          if (manutype === undefined) { manutype = "other"; }

          // Get alternative parameters from [oParams] if this is defined
          if (oParams !== undefined) {
            if ('manutype' in oParams) { manutype = oParams['manutype']; }
          }

          // Check if we need to take the table
          if ($(elTr).hasClass("table")) {
            elTr = $(el).closest("table");
          }
          // Get the view and edit values
          elView = $(el).find(".view-mode").first();
          elEdit = $(el).find(".edit-mode").first();

          // Action depends on the mode
          switch (sMode) {
            case "skip":
              return;
              break;
            case "edit":
              // Make sure all targetid's that need opening are shown
              $(elTr).find(".view-mode:not(.hidden)").each(function () {
                var elTarget = $(this).attr("targetid");
                var targeturl = $(this).attr("targeturl");

                frm = $(el).closest("form");
                data = frm.serializeArray();
                if (elTarget !== undefined && elTarget !== "") {
                  // Do we have a targeturl?
                  if (targeturl !== undefined && targeturl !== "") {
                    // Make a post to the targeturl
                    $.post(targeturl, data, function (response) {
                      // Action depends on the response
                      if (response === undefined || response === null || !("status" in response)) {
                        private_methods.errMsg("No status returned");
                      } else {
                        switch (response.status) {
                          case "ready":
                          case "ok":
                            if ("html" in response) {
                              // Show the HTML in the targetid
                              $("#" + elTarget).html(response['html']);
                            }
                            // In all cases: open the target
                            $("#" + elTarget).removeClass("hidden");
                            // And make sure typeahead works
                            ru.cesar.init_typeahead();
                            break;
                        }
                      }
                    });
                  } else {
                    // Just open the target
                    $("#" + elTarget).removeClass("hidden");
                  }
                }
              });
              // Go to edit mode
              $(elTr).find(".view-mode").addClass("hidden");
              $(elTr).find(".edit-mode").removeClass("hidden");
              // Make sure typeahead works here
              ru.cesar.init_typeahead();
              break;
            case "view":
            case "new":
              // Get any possible targeturl
              targeturl = $(el).attr("targeturl");
              targetid = $(el).attr("targetid");
              // If the targetid is specified, we need to get it from there
              if (targetid === undefined || targetid === "") {
                // No targetid specified: just open the target url
                window.location.href = targeturl;
              } else if (loc_bManuSaved) {
                loc_bManuSaved = false;
                // Refresh page
                window.location.href = window.location.href;
              } else {
                switch (manutype) {
                  case "goldlink":
                  case "goldnew":
                  case "newgoldlink":
                    targethead = $("#" + targetid);
                    break;
                  case "goldlinkclose":
                    targethead = $("#" + targetid).closest(".goldlink");
                    $(targethead).addClass("hidden");
                    $(elTr).find(".edit-mode").addClass("hidden");
                    $(elTr).find(".view-mode").removeClass("hidden");
                    return;
                  default:
                    targethead = $("#" + targetid).closest("tr.gold-head");
                    if (targethead !== undefined && targethead.length > 0) {
                      // Targetid is specified: check if we need to close
                      if (!$(targethead).hasClass("hidden")) {
                        // Close it
                        $(targethead).addClass("hidden");
                        return;
                      }
                    } else if ($("#" + targetid).attr("showing") !== undefined) {
                      if ($("#" + targetid).attr("showing") === "true") {
                        $("#" + targetid).attr("showing", "false");
                        $("#" + targetid).html("");
                        return;
                      }
                    }
                    break;
                }

                // There is a targetid specified, so make a GET request for the information and get it here
                data = [];
                // Check if there are any parameters in [oParams]
                if (oParams !== undefined) {
                  for (key in oParams) {
                    data.push({ 'name': key, 'value': oParams[key] });
                  }
                }

                $.get(targeturl, data, function (response) {
                  // Action depends on the response
                  if (response === undefined || response === null || !("status" in response)) {
                    private_methods.errMsg("No status returned");
                  } else {
                    switch (response.status) {
                      case "ready":
                      case "ok":
                      case "error":
                        if ("html" in response) {
                          // Show the HTML in the targetid
                          $("#" + targetid).html(response['html']);
                          // Make sure invisible ancestors show up
                          $("#" + targetid).closest(".hidden").removeClass("hidden");
                          // Indicate that we are showing here
                          $("#" + targetid).attr("showing", "true");

                          switch (manutype) {
                            case "goldsermon":
                              // Close any other edit-mode items
                              $(targethead).closest("table").find(".edit-mode").addClass("hidden");
                              // Open this particular edit-mode item
                              $(targethead).removeClass("hidden");
                              break;
                            case "goldlink":
                              $(el).closest("table").find(".edit-mode").addClass("hidden");
                              $(el).closest("table").find(".view-mode").removeClass("hidden");
                              $(elTr).find(".edit-mode").removeClass("hidden");
                              $(elTr).find(".view-mode").addClass("hidden");
                              break;
                            case "goldnew":
                              // Use the new standard approach for *NEW* elements
                              $("#" + targetid).closest(".subform").find(".edit-mode").removeClass("hidden");
                              $("#" + targetid).closest(".subform").find(".view-mode").addClass("hidden");
                              break;
                            default:
                              break;
                          }

                          // Check on specific modes
                          if (sMode === "new") {
                            $("#" + targetid).find(".edit-mode").removeClass("hidden");
                            $("#" + targetid).find(".view-mode").addClass("hidden");
                            // This is 'new', so don't show buttons cancel and delete
                            $("#" + targetid).find("a[mode='cancel'], a[mode='delete']").addClass("hidden");
                            // Since this is new, don't show fields that may not be shown for new
                            $("#" + targetid).find(".edit-notnew").addClass("hidden");
                            $("#" + targetid).find(".edit-new").removeClass("hidden");
                          } else {
                            // Just viewing means we can also delete...
                            // What about CANCEL??
                            // $("#" + targetid).find("a[mode='delete']").addClass("hidden");
                          }

                          // If there is an error, indicate this
                          if (response.status === "error") {
                            if ("msg" in response) {
                              if (typeof response['msg'] === "object") {
                                lHtml = []
                                lHtml.push("Errors:");
                                $.each(response['msg'], function (key, value) { lHtml.push(key + ": " + value); });
                                $(err).html(lHtml.join("<br />"));
                              } else {
                                $(err).html("Error: " + response['msg']);
                              }
                            } else {
                              $(err).html("<code>There is an error</code>");
                            }
                          }
                        } else {
                          // Send a message
                          $(err).html("<i>There is no <code>html</code> in the response from the server</i>");
                        }
                        break;
                      default:
                        // Something went wrong -- show the page or not?
                        $(err).html("The status returned is unknown: " + response.status);
                        break;
                    }
                  }
                  switch (manutype) {
                    case "goldlink":
                    case "goldnew":
                      break;
                    default:
                      // Return to view mode
                      $(elTr).find(".view-mode").removeClass("hidden");
                      $(elTr).find(".edit-mode").addClass("hidden");
                      // Hide waiting symbol
                      $(elTr).find(".waiting").addClass("hidden");
                      break;
                  }
                  // Perform init again
                  ru.cesar.init_typeahead();
                  ru.cesar.seeker.init_events();
                });

              }
              break;
            case "save":
              // Show waiting symbol
              $(elTr).find(".waiting").removeClass("hidden");

              // Make sure we know where the error message should come
              if ($(err).length === 0) { err = $(".err-msg").first(); }

              // Get any possible targeturl
              targeturl = $(el).attr("targeturl");
              targetid = $(el).attr("targetid");

              // What if no targetid is specified?
              if (targetid === undefined || targetid === "") {
                // Then we need the parent of our closest enclosing table
                targetid = $(el).closest("form").parent();
              } else {
                targetid = $("#" + targetid);
              }

              // Check
              if (targeturl === undefined) { $(err).html("Save: no <code>targeturl</code> specified"); bOkay = false }
              if (bOkay && targetid === undefined) { $(err).html("Save: no <code>targetid</code> specified"); }

              // Get the form data
              frm = $(el).closest("form");
              if (bOkay && frm === undefined) { $(err).html("<i>There is no <code>form</code> in this page</i>"); }

              // Either POST the request
              if (bOkay) {
                // Get the data into a list of k-v pairs
                data = $(frm).serializeArray();
                // Adapt the value for the [library] based on the [id] 
                // Try to save the form data: send a POST
                $.post(targeturl, data, function (response) {
                  // Action depends on the response
                  if (response === undefined || response === null || !("status" in response)) {
                    private_methods.errMsg("No status returned");
                  } else {
                    switch (response.status) {
                      case "error":
                        // Indicate there is an error
                        bOkay = false;
                        // Show the error in an appropriate place
                        if ("msg" in response) {
                          if (typeof response['msg'] === "object") {
                            lHtml = [];
                            lHtml.push("Errors:");
                            $.each(response['msg'], function (key, value) { lHtml.push(key + ": " + value); });
                            $(err).html(lHtml.join("<br />"));
                          } else {
                            $(err).html("Error: " + response['msg']);
                          }
                        } else if ("errors" in response) {
                          lHtml = [];
                          lHtml.push("<h4>Errors</h4>");
                          for (i = 0; i < response['errors'].length; i++) {
                            $.each(response['errors'][i], function (key, value) {
                              lHtml.push("<b>" + key + "</b>: </i>" + value + "</i>");
                            });
                          }
                          $(err).html(lHtml.join("<br />"));
                        } else if ("error_list" in response) {
                          lHtml = [];
                          lHtml.push("Errors:");
                          $.each(response['error_list'], function (key, value) { lHtml.push(key + ": " + value); });
                          $(err).html(lHtml.join("<br />"));
                        } else {
                          $(err).html("<code>There is an error</code>");
                        }
                        break;
                      case "ready":
                      case "ok":
                        if ("html" in response) {
                          // Show the HTML in the targetid
                          $(targetid).html(response['html']);
                          // Signal globally that something has been saved
                          loc_bManuSaved = true;
                          // If an 'afternewurl' is specified, go there
                          if ('afternewurl' in response && response['afternewurl'] !== "") {
                            window.location = response['afternewurl'];
                            bReloading = true;
                          } else {
                            // nothing else yet
                          }
                        } else {
                          // Send a message
                          $(err).html("<i>There is no <code>html</code> in the response from the server</i>");
                        }
                        break;
                      default:
                        // Something went wrong -- show the page or not?
                        $(err).html("The status returned is unknown: " + response.status);
                        break;
                    }
                  }
                  if (!bReloading && bOkay) {
                    // Return to view mode
                    $(elTr).find(".view-mode").removeClass("hidden");
                    $(elTr).find(".edit-mode").addClass("hidden");
                    // Hide waiting symbol
                    $(elTr).find(".waiting").addClass("hidden");
                    // Perform init again
                    ru.cesar.seeker.init_events();
                  }
                });
              } else {
                // Or else stop waiting - with error message above
                $(elTr).find(".waiting").addClass("hidden");
              }

              break;
            case "cancel":
              // Make sure all targetid's that need closing are hidden
              $(elTr).find(".edit-mode:not(.hidden)").each(function () {
                var elTarget = $(this).attr("targetid");
                if (elTarget !== undefined && elTarget !== "") {
                  $("#" + elTarget).addClass("hidden");
                }
              });
              // Go to view mode without saving
              $(elTr).find(".view-mode").removeClass("hidden");
              $(elTr).find(".edit-mode").addClass("hidden");
              break;
            case "delete":
              // Do we have an afterurl?
              afterurl = $(el).attr("afterurl");

              // Check if we are under a delete-confirm
              if ($(el).closest("div[delete-confirm]").length === 0) {
                // Ask for confirmation
                // NOTE: we cannot be more specific than "item", since this can be manuscript or sermongold
                if (!confirm("Do you really want to remove this item?")) {
                  // Return from here
                  return;
                }
              }
              // Show waiting symbol
              $(elTr).find(".waiting").removeClass("hidden");

              // Get any possible targeturl
              targeturl = $(el).attr("targeturl");

              // Determine targetid from own
              targetid = $(el).closest(".gold-head");
              targethead = $(targetid).prev();

              // Check
              if (targeturl === undefined) { $(err).html("Save: no <code>targeturl</code> specified"); bOkay = false }

              // Get the form data
              frm = $(el).closest("form");
              if (bOkay && frm === undefined) { $(err).html("<i>There is no <code>form</code> in this page</i>"); }
              // Either POST the request
              if (bOkay) {
                // Get the data into a list of k-v pairs
                data = $(frm).serializeArray();
                // Add the delete mode
                data.push({ name: "action", value: "delete" });

                // Try to delete: send a POST
                $.post(targeturl, data, function (response) {
                  // Action depends on the response
                  if (response === undefined || response === null || !("status" in response)) {
                    private_methods.errMsg("No status returned");
                  } else {
                    switch (response.status) {
                      case "ready":
                      case "ok":
                        // Do we have an afterurl?
                        // If an 'afternewurl' is specified, go there
                        if ('afterdelurl' in response && response['afterdelurl'] !== "") {
                          window.location = response['afterdelurl'];
                        } else if (afterurl === undefined || afterurl === "") {
                          // Delete visually
                          $(targetid).remove();
                          $(targethead).remove();
                        } else {
                          // Make sure we go to the afterurl
                          window.location = afterurl;
                        }
                        break;
                      case "error":
                        if ("html" in response) {
                          // Show the HTML in the targetid
                          $(err).html(response['html']);
                          // If there is an error, indicate this
                          if (response.status === "error") {
                            if ("msg" in response) {
                              if (typeof response['msg'] === "object") {
                                lHtml = []
                                lHtml.push("Errors:");
                                $.each(response['msg'], function (key, value) { lHtml.push(key + ": " + value); });
                                $(err).html(lHtml.join("<br />"));
                              } else {
                                $(err).html("Error: " + response['msg']);
                              }
                            } else {
                              $(err).html("<code>There is an error</code>");
                            }
                          }
                        } else {
                          // Send a message
                          $(err).html("<i>There is no <code>html</code> in the response from the server</i>");
                        }
                        break;
                      default:
                        // Something went wrong -- show the page or not?
                        $(err).html("The status returned is unknown: " + response.status);
                        break;
                    }
                  }
                  // Return to view mode
                  $(elTr).find(".view-mode").removeClass("hidden");
                  $(elTr).find(".edit-mode").addClass("hidden");
                  // Hide waiting symbol
                  $(elTr).find(".waiting").addClass("hidden");
                  // Perform init again
                  ru.cesar.seeker.init_events();
                });
              } else {
                // Or else stop waiting - with error message above
                $(elTr).find(".waiting").addClass("hidden");
              }


              break;
          }
        } catch (ex) {
          private_methods.errMsg("process_edit", ex);
        }
      },



      var_down: function() {private_methods.var_move(this, 'down');},
      var_up: function () { private_methods.var_move(this, 'up'); },


    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

