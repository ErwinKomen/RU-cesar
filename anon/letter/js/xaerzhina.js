var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;

(function ($) {
  $(function () {
    $(document).ready(function () {
      // Initialize event listeners
      ru.xaerzhina.init_event_listeners();
    });
  });
})(django.jQuery);

// based on the type, action will be loaded

// var $ = django.jQuery.noConflict();

var ru = (function ($, ru) {
  "use strict";

  ru.xaerzhina = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "",
        loc_divErr = "xaerzhina_err",
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
            layout = "xaerzhina/layout.html",
            tr_story = "",
            tr_collapse = "";

        try {
          // Initialize story events
          ru.xaerzhina.init_story_events();

          if ($(".hidden.one-story-sample").length === 0) {
            return;
          }
          // Read the sample html
          tr_story = $(".hidden.one-story-sample")[0].outerHTML;
          elTbody = $("table.table tbody").first();



          // Read the xaerzhina.json file
          datasource = $("#data-source").attr("href");
          $.getJSON(datasource, function (data) {
            var i = 0,
                tr_a = "",
                tr_b = "",
                id = "",
                label = "",
                che = "",
                name = "";
            // set the date correctly
            $(".lastedit").html("(ЮхаметтахІоьттина: " + data.lastedit + ")");
            // Walk the stories
            for (i = 0; i < data.stories.length; i++) {
              id = data.stories[i].id;
              label = data.stories[i].ch.toString() + "." + data.stories[i].part.toString();
              name = data.stories[i].name;
              che = data.stories[i].che;
              // Create elements
              tr_a = tr_story.replaceAll("{{id}}", id).replaceAll("{{label}}", label);
              tr_a = tr_a.replaceAll("{{name}}", name).replaceAll("{{che}}", che).replace("one-story-sample", "one-story");
              // Create and append element for this story
              $(tr_a).appendTo(elTbody);
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
        } catch (ex) {
          private_methods.errMsg("init_event_listeners", ex);
        }
      },

      /**
       *  init_story_events
       *      Initialize story events
       *
       */
      init_story_events() {
        try {
          // Bind on the language choice changes radio buttons
          $(".language-choice input[type=radio]").bind('change', ru.xaerzhina.lang_change);
          // Show the first language only
          $(".story").addClass("hidden");
          $(".story[language=che]").removeClass("hidden");
        } catch (ex) {
          private_methods.errMsg("init_story_events", ex);
        }
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
       *  load_story
       *      Load the indicated story
       *
       */
      load_story: function(sId) {
        var sStory = "xaerzhina/diicar_{{id}}.html",
            sLayout = "xaerzhina/container.html",
            elContainer = null;
        try {
          // Get the right link to the story
          sStory = sStory.replace("{{id}}", sId);
          // Load the container into <section class='container'>
          elContainer = $("section.container").first();
          $(elContainer).load(sLayout, { story: sStory }, function (data, status, jqXGR) {
            var x = 1;
            switch (status) {
              case "success":
                // Put the data on the right place
                $(elContainer).html(data);
                // Find the place where to load the story itself
                $(".story-contents").load(sStory, function (a, b, c) {
                  // Make sure events are initialized again
                  ru.xaerzhina.init_story_events();
                });
                break;
              default:
                private_methods.errMsg("Load story yields status: " + status);
                break;
            }
          });
        } catch (ex) {
          private_methods.errMsg("load_story", ex);
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

