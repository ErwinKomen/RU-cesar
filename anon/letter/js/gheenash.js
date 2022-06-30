var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

(function ($) {
  $(function () {
    $(document).ready(function () {
      // Initialize event listeners
      ru.gheenash.init_event_listeners();
    });
  });
})(django.jQuery);

// based on the type, action will be loaded

// var $ = django.jQuery.noConflict();

var ru = (function ($, ru) {
  "use strict";

  ru.gheenash = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        loc_divErr = "gheenash_err",
        oSyncTimer = null;


    // Private methods specification
    var private_methods = {
      /**
       * methodNotVisibleFromOutside - example of a private method
       * @returns {String}
       */
      methodNotVisibleFromOutside: function () {
        return "something";
      },
      errMsg: function (sMsg, ex) {
        var sHtml = "Error in [" + sMsg + "]<br>" + ex.message;
        $("#" + loc_divErr).html(sHtml);
      }
    }

    // Public methods
    return {
      /**
       * init_event_listeners
       *    Initialize eent listeners for this module
       */
      init_event_listeners: function () {
        var datasource = "",
            elTbody = null,
            tr_story = "",
            tr_collapse = "";

        // Bind on the language choice changes radio buttons
        $(".language-choice input[type=radio]").bind('change', ru.gheenash.lang_change);
        // Show the first language only
        $(".story").addClass("hidden");
        $(".story").first().removeClass("hidden");

        // Read the sample html
        tr_story = $(".hidden.one-story-sample")[0].outerHTML;
        tr_collapse = $(".collapse.one-collapse-sample")[0].outerHTML;
        elTbody = $("table.table tbody").first();

        // Read the gheenash.json file
        datasource = $("#data-source").attr("href");
        $.getJSON(datasource, function (data) {
          var i = 0,
              tr_a = "",
              tr_b = "",
              id = "",
              label = "",
              name = "";
          // set the date correctly
          $(".lastedit").html("(Update: " + data.lastedit + ")");
          // Walk the stories
          for (i = 0; i < data.stories.length; i++) {
            id = data.stories[i].id;
            label = data.stories[i].label;
            name = data.stories[i].name;
            // Create elements
            tr_a = tr_story.replaceAll("{{id}}", id).replaceAll("{{label}}", label).replaceAll("{{name}}", name).replace("one-story-sample", "one-story");
            tr_b = tr_collapse.replaceAll("{{id}}", id).replaceAll("{{label}}", label).replaceAll("{{name}}", name).replace("one-collapse-sample", "");
            // Create and append element for this story
            $(tr_a).appendTo(elTbody);
            $(tr_b).appendTo(elTbody);
          }

          // Show pages that actually exist
          $("tr.one-story").each(function (idx, el) {
            var elAnchor = null,
                address = "";

            elAnchor = $(el).find("a").last();
            address = $(elAnchor).attr("href");

            $.ajax({
              type: 'HEAD',
              url: address,
              success: function () {
                // Show it
                $(el).removeClass("hidden");
              }
            })
          });

        });

      },

      /**
       *  view_switch
       *      Switch from one view to the other
       *
       */
      lang_change: function (ev) {
        var language = "";

        try {
          // Get the language
          language = ev.target.value;
          // Show that language and hide the others
          $(".story").addClass("hidden");
          $(".story[language='" + language + "']").removeClass("hidden");
        } catch (ex) {
          private_methods.errMsg("lang_change", ex);
        }
      },
    
      /**
       *  view_switch
       *      Switch from one view to the other
       *
       */
      view_switch: function (sOpen, sClose) {
        $("#" + sOpen).removeClass("hidden");
        $("#" + sClose).addClass("hidden");
        // Show/hide <li> elements
        $("li." + sOpen).removeClass("hidden");
        $("li." + sClose).addClass("hidden");
      }

    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

