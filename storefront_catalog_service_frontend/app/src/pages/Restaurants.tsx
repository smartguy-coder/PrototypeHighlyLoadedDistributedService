import { useState } from "react";
import { useNavigate } from "react-router";
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardMedia,
  CardActions,
  Typography,
  Chip,
  Button,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Rating,
} from "@mui/material";
import {
  Search as SearchIcon,
  AccessTime as AccessTimeIcon,
  LocationOn as LocationOnIcon,
} from "@mui/icons-material";
import { mockRestaurants } from "../data/mockData";

const cuisineTypes = [
  "All",
  "Italian",
  "Japanese",
  "Indian",
  "American",
  "Mexican",
  "Chinese",
];

export default function Restaurants() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");
  const [cuisineFilter, setCuisineFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState<"all" | "open" | "closed">(
    "all",
  );

  const filteredRestaurants = mockRestaurants.filter((restaurant) => {
    const matchesSearch =
      restaurant.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      restaurant.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCuisine =
      cuisineFilter === "All" || restaurant.cuisine === cuisineFilter;
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "open" && restaurant.isOpen) ||
      (statusFilter === "closed" && !restaurant.isOpen);
    return matchesSearch && matchesCuisine && matchesStatus;
  });

  return (
    <Box>
      {/* Filters */}
      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          gap: 2,
          mb: 4,
        }}
      >
        <TextField
          placeholder="Search restaurants..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ flex: 1, minWidth: 250 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon color="action" />
                </InputAdornment>
              ),
            },
          }}
        />
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Cuisine</InputLabel>
          <Select
            value={cuisineFilter}
            label="Cuisine"
            onChange={(e) => setCuisineFilter(e.target.value)}
          >
            {cuisineTypes.map((cuisine) => (
              <MenuItem key={cuisine} value={cuisine}>
                {cuisine}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl sx={{ minWidth: 120 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            label="Status"
            onChange={(e) =>
              setStatusFilter(e.target.value as "all" | "open" | "closed")
            }
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="open">Open</MenuItem>
            <MenuItem value="closed">Closed</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Restaurant Grid */}
      <Grid container spacing={3}>
        {filteredRestaurants.map((restaurant) => (
          <Grid size={{ xs: 12, sm: 6, lg: 4 }} key={restaurant.id}>
            <Card
              sx={{
                borderRadius: 3,
                boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                transition: "transform 0.2s, box-shadow 0.2s",
                opacity: restaurant.isOpen ? 1 : 0.7,
                "&:hover": {
                  transform: "translateY(-4px)",
                  boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
                },
              }}
            >
              <Box sx={{ position: "relative" }}>
                <CardMedia
                  component="img"
                  height="180"
                  image={restaurant.imageUrl}
                  alt={restaurant.name}
                  sx={{ objectFit: "cover" }}
                />
                <Chip
                  label={restaurant.isOpen ? "Open" : "Closed"}
                  color={restaurant.isOpen ? "success" : "default"}
                  size="small"
                  sx={{
                    position: "absolute",
                    top: 12,
                    right: 12,
                    fontWeight: 600,
                  }}
                />
              </Box>
              <CardContent sx={{ pb: 1 }}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    mb: 1,
                  }}
                >
                  <Typography variant="h6" fontWeight={600}>
                    {restaurant.name}
                  </Typography>
                  <Chip
                    label={restaurant.cuisine}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: "0.7rem" }}
                  />
                </Box>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    mb: 2,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    minHeight: 40,
                  }}
                >
                  {restaurant.description}
                </Typography>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                    mb: 1,
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center" }}>
                    <Rating
                      value={restaurant.rating}
                      precision={0.1}
                      size="small"
                      readOnly
                    />
                    <Typography
                      variant="body2"
                      fontWeight={600}
                      sx={{ ml: 0.5 }}
                    >
                      {restaurant.rating}
                    </Typography>
                  </Box>
                </Box>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                    color: "text.secondary",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <AccessTimeIcon fontSize="small" />
                    <Typography variant="body2">
                      {restaurant.deliveryTime}
                    </Typography>
                  </Box>
                  <Typography variant="body2">
                    Min: ${restaurant.minimumOrder}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 0.5,
                    mt: 1,
                    color: "text.secondary",
                  }}
                >
                  <LocationOnIcon fontSize="small" />
                  <Typography variant="body2" noWrap>
                    {restaurant.address}
                  </Typography>
                </Box>
              </CardContent>
              <CardActions sx={{ px: 2, pb: 2 }}>
                <Button
                  fullWidth
                  variant="contained"
                  disabled={!restaurant.isOpen}
                  onClick={() => navigate(`/restaurants/${restaurant.id}`)}
                  sx={{
                    background:
                      "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "&:hover": {
                      background:
                        "linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%)",
                    },
                    "&:disabled": {
                      background: "rgba(0,0,0,0.12)",
                    },
                  }}
                >
                  {restaurant.isOpen ? "View Menu" : "Currently Closed"}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {filteredRestaurants.length === 0 && (
        <Box
          sx={{
            textAlign: "center",
            py: 8,
            color: "text.secondary",
          }}
        >
          <Typography variant="h6">No restaurants found</Typography>
          <Typography variant="body2">
            Try adjusting your filters or search term
          </Typography>
        </Box>
      )}
    </Box>
  );
}
