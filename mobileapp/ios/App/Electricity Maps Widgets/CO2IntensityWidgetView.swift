//
//  CO2IntensityView.swift
//  Electricity Maps Widget
//
//  Created by Mads Nedergaard on 10/11/2023.
//

import Foundation
import SwiftUI
import UIKit
import WidgetKit

struct ViewSizeEntry: TimelineEntry {
  let date: Date
  let intensity: Int?
  let zone: String?

  static var placeholder: ViewSizeEntry {
    ViewSizeEntry(

      date: Date(),
      intensity: 123,
      zone: nil
    )
  }
}

struct CO2IntensityWidgetView: View {
    let entry: ViewSizeEntry
    
    @Environment(\.widgetFamily) var widgetFamily

  var body: some View {
      switch widgetFamily {
          case .systemSmall:
              SmallWidgetView(entry: entry)
          case .systemMedium:
              SmallWidgetView(entry: entry)
          case .accessoryRectangular:
            LockscreenRecWidgetView(entry: entry)
        case .accessoryCircular:
              CircularWidgetView()
          
          default:
              Text("Unsupported widget size")
          }
    
  }
}

struct CircularWidgetView: View {
    var body: some View {
        if #available(iOS 17.0, *) {
            ZStack {
                Image("electricitymaps-icon-white") // Your icon name here
                    .resizable()
                    .scaledToFit()
            }
            .containerBackground(for: .widget) {
                Color.black
            }
        } else {
            ZStack {
                Image("electricitymaps-icon-white")
                    .resizable()
                    .scaledToFit()
            }
            .background(Color.black)
        }
    }
}


struct LockscreenRecWidgetView: View {
    var entry: ViewSizeEntry
    
    var body: some View {
        if entry.zone != nil {
          VStack(alignment: .center) {
              HStack {
                  Text(String(entry.intensity ?? 0) + "g")
                      .font(.system(size: 30))
                  .fontWeight(.bold)              }
                Text("CO₂eq/kWh")
                    .font(.headline)

          }
          .padding(4)
          .padding([.horizontal], 10)
          .backgroundColor(for: entry)
          .overlay(
              RoundedRectangle(cornerRadius: 10) // Adjust the corner radius as needed
                  .stroke(Color.blue, lineWidth: 5) // Set the color and width of the border
          )
        } else {
          VStack(alignment: .center) {
            Text("⚡️")
            Text("Open widget settings")
              .font(.body)
              .multilineTextAlignment(.center)

          }
            .backgroundColor(for: entry)
        }
    }
}

struct SmallWidgetView: View {
    var entry: ViewSizeEntry
    
    var body: some View {
        if entry.zone != nil {
          VStack(alignment: .center) {

            VStack {
              Spacer()
              HStack {
                Text(String(entry.intensity ?? 0))
                  .font(.largeTitle)
                  .fontWeight(.heavy)
                  .foregroundColor(getTextColor(intensity: entry.intensity, type: "main"))
                Text("g")
                  .font(.system(.title))
                  .foregroundColor(getTextColor(intensity: entry.intensity, type: "main"))
              }
              .padding(.top)

              Text("CO₂eq/kWh")
                .font(.footnote)
                .foregroundColor(getTextColor(intensity: entry.intensity, type: "subtitle"))
                .opacity(0.75)

              Spacer()
            }
            HStack {
              Text("\(formatDate(entry.date)) · \(entry.zone ?? "?")")
                .font(.caption)
                .foregroundColor(Color(red: 0, green: 0, blue: 0, opacity: 0.4))
                .padding(.bottom, 5.0)
            }
              // TODO: Widget deep link to specific zone?
              // This depends on some changes to the app in an open PR, so let's park it for now.
            //.widgetURL(URL(string: "com.tmrow.electricitymap://zone/DE"))

          }

          .frame(maxWidth: .infinity, maxHeight: .infinity)
          // Custom function that allows us to support both ios17 and older
          .backgroundColor(for: entry)
        } else {
          VStack(alignment: .center) {
            Text("⚡️")
            Text("Open widget settings")
              .font(.body)
              .multilineTextAlignment(.center)

          }
        }
    }
}

struct View_co2_Previews: PreviewProvider {
  static var previews: some View {
    Group {
        CO2IntensityWidgetView(
        entry: ViewSizeEntry(
          date: Date(),
          intensity: 290,
          zone: "DE")
      )
      .previewContext(WidgetPreviewContext(family: .accessoryRectangular))
    }
  }
}
