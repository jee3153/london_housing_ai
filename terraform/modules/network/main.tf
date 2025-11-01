# subnetwork automode is on by default - it's creating subnetwork automatically
resource "google_compute_network" "vpc_network" {
  name = "london-housing-vpc"
}
