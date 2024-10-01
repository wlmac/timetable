group "A" { # Orange group, now on the right side
  x = 930
  y = 500
  rotate = 90
  colour = "#decaa1"

  desk "1-2" {
    x = 0
    y = -105 * 0
  }
  desk "3-4" {
    x = 0
    y = -105 * 1
  }
  desk "5-6" {
    x = 0
    y = -105 * 2
  }
  desk "7-8" {
    x = 0
    y = -105 * 3
  }
  desk "9-10" {
    x = 0
    y = -105 * 4
  }
}

group "B" { # Cyan group, bottom most
  x = 230
  y = 620
  colour = "#93ead8"

  desk "23-24" {
    x = 105 * 0
    y = 0
  }
  desk "25-26" {
    x = 105 * 1
    y = 0
  }
  desk "27-28" {
    x = 105 * 2
    y = 0
  }
  desk "29-30" {
    x = 105 * 3
    y = 0
  }
  desk "31-32" {
    x = 105 * 4
    y = 0
  }
  desk "33" {
    x = 105 * 5
    y = 0
  }
}

group "C" { # Yellow group, left
  x = 230
  y = 240
  colour = "#f1ee84"

  desk "54-55" {
    x = 116
    y = 55
    rotate = 90
  }
  desk "56-57" {
    x = 116
    y = 145
    rotate = 90
  }
  desk "58-59" {
    x = 150  // Adjusted to prevent overlap
    y = 235
  }
  desk "60-61" {
    x = 60  // Adjusted to prevent overlap
    y = 235
  }
  desk "62-63" {
    x = 184  // Adjusted to prevent overlap
    y = 145
    rotate = -90
  }
  desk "64-65" {
    x = 184  // Adjusted to prevent overlap
    y = 235
    rotate = -90
  }
  desk "52-53" {
    x = 150  // Adjusted to prevent overlap
    y = 0
  }
  desk "50-51" {
    x = 60  // Adjusted to prevent overlap
    y = 0
  }
}

group "D" { # Green group, right
  x = 570
  y = 240
  colour = "#9de1b7"

  desk "34-35" {
    x = 116
    y = 145
    rotate = 90
  }
  desk "36-37" {
    x = 150
    y = 235
  }
  desk "38-39" {
    x = 60  // Adjusted to prevent overlap
    y = 235
  }
  desk "40-41" {
    x = 184  // Adjusted to prevent overlap
    y = 145
    rotate = -90
  }
  desk "42-43" {
    x = 184  // Adjusted to prevent overlap
    y = 235
    rotate = -90
  }
  desk "44-45" {
    x = 116  // Adjusted to prevent overlap
    y = 55
    rotate = 90
  }

  desk "46-47" {
    x = 60  // Adjusted to prevent overlap
    y = 0
  }
  desk "48-49" {
    x = 150  // Adjusted to prevent overlap
    y = 0
  }
}

group "E" { # Top Red group
  x = 230
  y = 50
  colour = "#cab5b7"

  desk "11-12" {
    x = 105 * 0
    y = 0
  }
  desk "13-14" {
    x = 105 * 1
    y = 0
  }
  desk "15-16" {
    x = 105 * 2
    y = 0
  }
  desk "17-18" {
    x = 105 * 3
    y = 0
  }
  desk "19-20" {
    x = 105 * 4
    y = 0
  }
  desk "21-22" {
    x = 105 * 5
    y = 0
  }
}