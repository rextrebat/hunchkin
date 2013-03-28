'use strict';

/* Controllers */

angular.module(
        'hunchkin', ['ngSanitize']).directive('priceslider', function() {
  return {
    restrict: 'A',
    link:function(scope, element, attrs){
        element.slider({
        range: true,
        min: 0,
        max: 1000,
        step: 20,
        values: [ 20, 1400 ],
        slide: function( event, ui ) {
            $( "#filter_price" ).val( "$" + ui.values[ 0 ] + " - $" + ui.values[ 1 ] );
        },
        stop: function( event, ui ) {
            $( "#filter_price_min").val(ui.values[0]);
            $( "#filter_price_max").val(ui.values[1]);
            scope.filter_price_min = ui.values[0];
            scope.filter_price_max = ui.values[1];
            scope.$apply(scope.updateSelection());
        }
      });
      $( "#filter_price" ).val( "$" + $( "#price-slider" ).slider( "values", 0 ) +
        " - $" + $( "#price-slider" ).slider( "values", 1 ) );
      //$( "#filter_price_min" ).val($( "#price-slider" ).slider( "values", 0 ) );
      //$( "#filter_price_max" ).val($( "#price-slider" ).slider( "values", 1 ) );
    }
  }
});

function HotelRecoCtrl($scope, $http) {

    $scope.ratingHTML = function(star_rating) {
        var full_stars = Math.floor(star_rating);
        var half_star = star_rating > full_stars;
        var total_stars = 5;
        var html = '';
        for (var i=0; i<full_stars; i++){
            html += '<i class="icon-star"></i>';
        }
        if (half_star){
            html += '<i class="icon-star-half"></i>';
            full_stars += 1
        }
        for (i=0; i<(total_stars - full_stars); i++){
            html += '<i class="icon-star-empty"></i>';
        }
        return html;
    };

    $scope.priceHTML = function(avail_response) {
        var avail_text = "";
        var span_class = "label";
        if (avail_response != undefined && avail_response.available == true){
            avail_text = "$" + avail_response.low_rate.toString() + " and up";
            if (avail_response.low_rate > $scope.filter_price_max){
                span_class += " label-important";
            }
            else {
                span_class += " label-info";
            }
        }
        else {
            avail_text = "Unavailable";
            span_class += " label-important";
        }
        return '<span class="' + span_class + '">' + avail_text + '</span>'
    };

    $scope.updateSelection = function() {
        /*
        * Create a selection of hotels based on model parameters
        * 1. Apply Filters
        * 2. Sort
        * 3. Limit
        * 4. Get Availabilty
        */

        $scope.selection = $scope.hotels.slice();
        //apply Filters
        for (var i = 0; i < $scope.selection.length; i++){
            var low_rate = $scope.selection[i].LowRate;
            if (low_rate < $scope.filter_price_min || low_rate > $scope.filter_price_max){
                $scope.selection.splice(i,1);
                i -= 1;
            }
        }
        $scope.selection.sort(function(a, b) {
            return b.aggregates - a.aggregates
            });
        $scope.selection = $scope.selection.slice(0, $scope.limit);
        var avail_list = [];
        for (var i = 0; i < $scope.selection.length; i++) {
            if ($scope.selection[i].avail_response == undefined){
                avail_list.push($scope.selection[i].hotel_id)
            }
        }
        if (avail_list.length > 0){
            $http.get("search_results_avail?hotel_ids=" + avail_list.join(",") +
                    "&date_from=" + encodeURIComponent($scope.date_from) +
                    "&date_to=" + encodeURIComponent($scope.date_to)).success(function(data) {
                        for (var hotel_id in data){
                            for ( var j=0; j < $scope.selection.length; j++){
                                if ($scope.selection[j].hotel_id == hotel_id){
                                    $scope.selection[j].avail_response = data[hotel_id];
                                    $scope.hotels[$scope.selection[j].array_offset].avail_response = data[hotel_id];
                                }
                            }
                        }


                    });
        }


    }

    $scope.limit = 5;

    $http.get("search_results_a_ctrl?dest_id=" + $scope.region_id + 
            "&hotel_id=" + $scope.base_hotel_id).success(function(data) {
                $scope.hotels = data;
                /*
                for (i=0; i < $scope.hotels.length; i++){
                    $scope.hotels[i].avail_response = "";
                }
                */
                $http.get("search_results_a_initial_price_limit?region_id=" + $scope.region_id +
                        "&ref_hotel_id=" + $scope.base_hotel_id).success(function(data) {
                            $scope.filter_price_min = 0;
                            $scope.filter_price_max = data
                            $("#price-slider").slider( "option", "values", [
                                $scope.filter_price_min, $scope.filter_price_max
                                ]);
                            $( "#filter_price" ).val( "$" + $( "#price-slider" ).slider( "values", 0 ) +
                                " - $" + $( "#price-slider" ).slider( "values", 1 ) );
                            $scope.updateSelection();
                        });
            });

    $http.get("search_results_a_region_coords?region_id=" +
            $scope.region_id).success(function(data) {
                $scope.region_lat = data.latitude;
                $scope.region_long = data.longitude;
            });

    $scope.postSurvey = function() {
        FB.api("/me", function(response) {
            if (!response || response.error) {
                alert("Not logged in");
                } else {
                    var hotel_ids = [];
                    for (i=0; i<$scope.selection.length; i++){
                        hotel_ids.push($scope.selection[i].hotel_id);
                    }
                    $http({
                        url: "http://hk.jumpingcrab.com:5000/social/save-survey",
                        method: "POST",
                        data: {
                            "region_id": $scope.region_id,
                            "hotel_ids": hotel_ids.toString(),
                            "created_by_id": response.id,
                            "created_by_first_name": response.first_name,
                            "created_by_last_name": response.last_name,
                            "created_by_name": response.name
                        }
                    }).
                    success(function(data, status) {
                        var survey_id = data;
                        alert("Created survey: " + survey_id);
                    });
            }
        });
    }

}

