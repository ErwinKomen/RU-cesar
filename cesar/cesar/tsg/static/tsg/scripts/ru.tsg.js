var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

(function ($) {
  $(function () {
    $(document).ready(function () {
      // Initialize event listeners
      //ru.basic.init_events();
      // ru.basic.init_typeahead();

      // Initialize Bootstrap popover
      // Note: this is used when hovering over the question mark button
      $('[data-toggle="popover"]').popover();
    });
  });
})(django.jQuery);



// based on the type, action will be loaded

// var $ = django.jQuery.noConflict();

var ru = (function ($, ru) {
  "use strict";

  ru.tsg = (function ($, config) {
    // Define variables for ru.basic here
    var loc_divErr = "basic_err",
      loc_urlStore = "",      // Keep track of URL to be shown
      loc_progr = [],         // Progress tracking
      loc_sWaiting = " <span class=\"glyphicon glyphicon-refresh glyphicon-refresh-animate\"></span>",
      loc_bManuSaved = false,
      KEYS = {
        BACKSPACE: 8, TAB: 9, ENTER: 13, SHIFT: 16, CTRL: 17, ALT: 18, ESC: 27, SPACE: 32, PAGE_UP: 33, PAGE_DOWN: 34,
        END: 35, HOME: 36, LEFT: 37, UP: 38, RIGHT: 39, DOWN: 40, DELETE: 46
      },
      dummy = 1;

    // Private methods specification
    var private_methods = {
      /**
       * aaaaaaNotVisibleFromOutside - example of a private method
       * @returns {String}
       */
      aaaaaaNotVisibleFromOutside: function () {
        return "something";
      },

      /** 
       *  errClear - clear the error <div>
       */
      errClear: function () {
        $("#" + loc_divErr).html("");
      },

      /** 
       *  errMsg - show error message in <div> loc_divErr
       */
      errMsg: function (sMsg, ex) {
        var sHtml = "Error in [" + sMsg + "]<br>";
        if (ex !== undefined && ex !== null) {
          sHtml = sHtml + ex.message;
        }
        $("#" + loc_divErr).html(sHtml);
      }


    }
    // Public methods
    return {

      /* handle_delete
       *
       * Process deleting of a handle
       *
       */
      handle_delete: function (elStart) {
        var targeturl = "",
            redirecturl = "",
            data = null,
            frm = null;
        try {
          // Try to get the targeturl and the form
          targeturl = $(elStart).attr("targeturl");
          frm = $(elStart).closest(".tsghandle-top").find("form").first();
          data = frm.serializeArray();

          // Call the matter
          // Do we have a targeturl?
          if (targeturl !== undefined && targeturl !== "") {
            // Make a post to the targeturl
            $.post(targeturl, data, function (response) {
              // Action depends on the response
              if (response === undefined || response === null || response.status === undefined) {
                private_methods.errMsg("No status returned");
              } else {
                switch (response.status) {
                  case "ready":
                  case "ok":
                    // If all went well, we need to redirect
                    redirecturl = response.redirecturl;
                    window.location = redirecturl;
                    break;
                }
              }
            });
          } else {
            // Just open the target
            private_methods.errMsg("No targeturl specified");
          }


        } catch (ex) {
          private_methods.errMsg("handle_delete", ex);
        }
      }

      // LAST POINT
    }
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

