<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { fallbackPostsData, fallbackSite } from "./fallbackSite";
import {
  Ambulance,
  ArrowLeft,
  ArrowRight,
  Baby,
  BedDouble,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Cross,
  Eye,
  Facebook,
  HeartPulse,
  Mail,
  MapPin,
  Menu,
  Newspaper,
  Phone,
  Scissors,
  Search,
  Send,
  ShieldCheck,
  Stethoscope,
  X,
} from "lucide-vue-next";

const route = useRoute();
const router = useRouter();
const site = ref(fallbackSite);
const visitorCount = ref(4022694);
const postsData = ref(fallbackPostsData());
const postDetail = ref(null);
const pageDetail = ref(null);
const selectedService = ref(null);
const csrfTokenValue = ref("");
const loading = ref(false);
const isNavigating = ref(false);
const menuOpen = ref(false);
const searchText = ref(route.query.q || "");
const appointmentStatus = ref(null);
const appointmentLoading = ref(false);
const aimNssfOpen = ref(false);
const aimNssfChecklistOpen = ref(false);

/* ── Lightbox (Facebook-style image viewer) ── */
const lightboxOpen = ref(false);
const lightboxImages = ref([]);
const lightboxIndex = ref(0);
const postBodyRef = ref(null);
let touchStartX = 0;
let touchDeltaX = 0;
const form = reactive({
  name: "",
  phone: "",
  email: "",
  reason: "",
  department: "Outpatient Care",
  datetime: "",
});

const aimNssfUpdate = {
  title: "ការដាក់ឱ្យដំណើរការម៉ាស៊ីនផ្ទៀងផ្ទាត់ស្វ័យប្រវត្តិ ប.ស.ស (AIM NSSF)",
  subtitle: "មន្ទីរពេទ្យបង្អែកខេត្តកំពង់ឆ្នាំង បានបំពាក់ម៉ាស៊ីនស្វ័យប្រវត្តិដើម្បីសម្រួលសេវាជូនអ្នកជំងឺ",
  status: "កំពុងដំណើរការធម្មតា (Active)",
  location: "ច្រកចុះឈ្មោះពិនិត្យជំងឺក្រៅ (OPD Registration)",
  date: "31 AUG 2026",
  stepsTitle: "របៀបប្រើប្រាស់ម៉ាស៊ីន AIM",
  steps: [
    {
      title: "ស្កេនកាត ប.ស.ស ឬ អត្តសញ្ញាណប័ណ្ណ",
      desc: "ដាក់កាតសម្គាល់ខ្លួន ឬកាត ប.ស.ស របស់អ្នកនៅលើកន្លែងស្កេនរបស់ម៉ាស៊ីន",
    },
    {
      title: "ផ្ទៀងផ្ទាត់អត្តសញ្ញាណ",
      desc: "ផ្ទៀងផ្ទាត់ស្នាមម្រាមដៃ ឬទិន្នន័យផ្ទាល់ខ្លួនតាមការណែនាំលើអេក្រង់",
    },
    {
      title: "ទទួលបង្កាន់ដៃចូលពិនិត្យ",
      desc: "ម៉ាស៊ីននឹងចេញប័ណ្ណលេខរង់ចាំ ឬបញ្ជាក់សិទ្ធិ ដើម្បីចូលជួបគ្រូពេទ្យភ្លាមៗ",
    },
  ],
  benefitsTitle: "អត្ថប្រយោជន៍ចម្បង",
  benefits: [
    "កាត់បន្ថយពេលវេលារង់ចាំកំណត់អត្តសញ្ញាណបានលឿនជាងមុន",
    "ធានាសិទ្ធិពេញលេញជូនដល់សមាជិក ប.ស.ស ទាំងអស់",
    "ទប់ស្កាត់ការក្លែងបន្លំ និងភាពមិនប្រក្រតី",
    "ជួយឱ្យដំណើរការចុះឈ្មោះអ្នកជំងឺមានភាពរហ័ស និងច្បាស់លាស់",
  ],
  notes: [
    "សូមយកកាត ប.ស.ស ឬអត្តសញ្ញាណប័ណ្ណមកជាមួយពេលមកពិនិត្យ",
    "ប្រសិនបើមានបញ្ហាក្នុងការប្រើម៉ាស៊ីន សូមស្នើសុំជំនួយពីបុគ្គលិកនៅច្រកចុះឈ្មោះ",
  ],
};

const aimNssfDocuments = ref([
  {
    title: "ប័ណ្ណសមាជិក ប.ស.ស ឬ App",
    desc: "កាតសមាជិក ប.ស.ស ឬ បើក QR Code ក្នុងកម្មវិធី NSSF Member App",
    checked: true,
  },
  {
    title: "អត្តសញ្ញាណប័ណ្ណសញ្ជាតិខ្មែរ (ID Card)",
    desc: "សូមយកឯកសារផ្ទៀងផ្ទាត់អត្តសញ្ញាណ និងត្រូវមានសុពលភាព",
    checked: true,
  },
  {
    title: "លេខទូរស័ព្ទមានសុពលភាព",
    desc: "សម្រាប់ទំនាក់ទំនង ឬជំនួយបន្ថែមពីបុគ្គលិកចុះឈ្មោះ",
    checked: false,
  },
]);

const aimNssfReadyCount = computed(() => aimNssfDocuments.value.filter((item) => item.checked).length);
const isAimNssfPost = computed(() => {
  const post = postDetail.value?.post;
  if (!post) return false;
  const text = `${post.title || ""} ${post.body || ""} ${post.category?.name || ""}`.toLowerCase();
  return text.includes("aim") || text.includes("nssf") || text.includes("ប.ស.ស");
});

const pathMode = computed(() => {
  if (route.path.startsWith("/about")) return "about";
  if (route.path.startsWith("/contact")) return "contact";
  if (route.path.startsWith("/services/")) return "service";
  if (route.path.startsWith("/post/")) return "post";
  if (route.path.startsWith("/page/")) return "page";
  if (route.path.startsWith("/news") || route.path.startsWith("/updates")) return "news";
  if (route.path.startsWith("/category/") || route.path.startsWith("/search")) return "news";
  return "home";
});

const isLanding = computed(() => route.path === "/");

const categoryId = computed(() => {
  if (!route.path.startsWith("/category/")) return null;
  return Number(route.params.id);
});

const activeCategory = computed(() => {
  if (!categoryId.value) return null;
  return postsData.value.categories.find((item) => item.id === categoryId.value);
});

const pageTitle = computed(() => {
  if (route.path.startsWith("/search")) return `Search: ${route.query.q || ""}`;
  if (activeCategory.value) return activeCategory.value.name;
  return "Latest News";
});

const updatesHeading = computed(() => {
  if (route.path.startsWith("/search")) return `Search: ${route.query.q || ""}`;
  if (activeCategory.value) return activeCategory.value.name;
  if (route.path.startsWith("/news") || route.path.startsWith("/updates")) return "ព័ត៌មាន និងសេចក្តីជូនដំណឹងទាំងអស់ (All News)";
  return "Hospital News & Announcements";
});
const homePosts = computed(() => postsData.value.posts.slice(0, 5));
const featuredPost = computed(() => (isLanding.value ? homePosts.value[0] : null));
const updatePosts = computed(() => {
  if (isLanding.value) {
    return homePosts.value.slice(1, 5); // Max 4 in grid + 1 featured = 5 posts total on home page
  }
  return postsData.value.posts;
});
const services = computed(() => site.value?.services || []);
const emergencyServiceTitles = new Set(["Emergency Ambulance 24/7", "Emergency & ICU", "Inpatient Care / IPD"]);
const emergencyServices = computed(() => services.value.filter((service) => emergencyServiceTitles.has(service.title)));
const regularServices = computed(() => services.value.filter((service) => !emergencyServiceTitles.has(service.title)));
const activeService = computed(() => {
  if (pathMode.value !== "service") return null;
  return services.value.find((service) => serviceSlug(service) === route.params.slug) || null;
});
const leaders = computed(() => site.value?.leaders || []);
const director = computed(() => leaders.value[0] || null);
const viceLeaders = computed(() => leaders.value.slice(1));
const contact = computed(() => site.value?.contact || {});
// Temporarily hide the Facebook feed. Set this back to true when the feature is needed again.
const facebookFeedEnabled = true;
// Temporarily hide the category filter pills. Set this back to true when ready to use again.
const categoryPillsEnabled = false;
// Temporarily hide the news search. Set this back to true when ready to use again.
const searchEnabled = false;
const showFacebookFeed = computed(() => facebookFeedEnabled && isLanding.value && Boolean(contact.value?.facebook));
const facebookFeedUrl = computed(() => {
  if (!contact.value?.facebook) return "";
  const params = new URLSearchParams({
    href: contact.value.facebook,
    tabs: "timeline",
    width: "500",
    height: "900",
    small_header: "true",
    adapt_container_width: "false",
    hide_cover: "true",
    show_facepile: "false",
  });
  return `https://www.facebook.com/plugins/page.php?${params.toString()}`;
});

const memoryCache = {
  site: null,
  posts: new Map(),
  postDetail: new Map(),
  pageDetail: new Map(),
};

function csrfToken() {
  if (csrfTokenValue.value) return csrfTokenValue.value;
  return document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "";
}

async function ensureCsrfToken() {
  const embedded = csrfToken();
  if (embedded) return embedded;
  const data = await fetchJson("/api/csrf");
  csrfTokenValue.value = data.csrfToken || "";
  return csrfTokenValue.value;
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function loadSite(force = false) {
  if (memoryCache.site && !force) {
    site.value = memoryCache.site;
    if (memoryCache.site.visitorCount) {
      visitorCount.value = memoryCache.site.visitorCount;
    }
    return;
  }
  try {
    const data = await fetchJson("/api/site");
    memoryCache.site = data;
    site.value = data;
    if (data.visitorCount) {
      visitorCount.value = data.visitorCount;
    }
  } catch (error) {
    if (!site.value) {
      site.value = fallbackSite;
    }
  }
}

async function loadPosts() {
  const params = new URLSearchParams();
  params.set("page", route.query.page || "1");
  const limit = isLanding.value ? "5" : "12";
  params.set("per_page", limit);
  if (route.query.q) params.set("q", route.query.q);
  if (categoryId.value) params.set("category_id", String(categoryId.value));
  const cacheKey = params.toString();

  if (memoryCache.posts.has(cacheKey)) {
    postsData.value = memoryCache.posts.get(cacheKey);
  }

  try {
    const data = await fetchJson(`/api/posts?${cacheKey}`);
    memoryCache.posts.set(cacheKey, data);
    postsData.value = data;
  } catch (error) {
    if (!memoryCache.posts.has(cacheKey)) {
      postsData.value = fallbackPostsData();
    }
  }
}

async function loadPostDetail() {
  if (pathMode.value !== "post") {
    postDetail.value = null;
    return;
  }
  const id = String(route.params.id || "");
  if (memoryCache.postDetail.has(id)) {
    postDetail.value = memoryCache.postDetail.get(id);
    return;
  }
  try {
    const data = await fetchJson(`/api/posts/${id}`);
    memoryCache.postDetail.set(id, data);
    postDetail.value = data;
  } catch (error) {
    postDetail.value = null;
  }
}

async function loadPageDetail() {
  if (pathMode.value !== "page") {
    pageDetail.value = null;
    return;
  }
  const slug = String(route.params.slug || "");
  if (memoryCache.pageDetail.has(slug)) {
    pageDetail.value = memoryCache.pageDetail.get(slug);
    return;
  }
  try {
    const data = await fetchJson(`/api/pages/${slug}`);
    memoryCache.pageDetail.set(slug, data.page);
    pageDetail.value = data.page;
  } catch (error) {
    pageDetail.value = null;
  }
}

let navCounter = 0;
async function loadAll() {
  const currentNav = ++navCounter;
  isNavigating.value = true;
  try {
    const promises = [loadSite()];
    if (pathMode.value === "home" || pathMode.value === "news") {
      promises.push(loadPosts());
    }
    if (pathMode.value === "post") {
      promises.push(loadPostDetail());
    } else {
      postDetail.value = null;
    }
    if (pathMode.value === "page") {
      promises.push(loadPageDetail());
    } else {
      pageDetail.value = null;
    }
    await Promise.all(promises);
  } finally {
    if (currentNav === navCounter) {
      isNavigating.value = false;
      loading.value = false;
    }
  }
}

function goSearch() {
  const q = searchText.value.trim();
  router.push(q ? { path: "/search", query: { q } } : "/");
  menuOpen.value = false;
}

function setPage(page) {
  router.push({ path: route.path, query: { ...route.query, page } });
}

function phoneHref(phone) {
  return `tel:${String(phone).replace(/[^\d+]/g, "")}`;
}

function serviceSlug(service) {
  return String(service.title || "")
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function servicePath(service) {
  return `/services/${serviceSlug(service)}`;
}

function openService(service) {
  if (!service.details) return;
  selectedService.value = service;
}

function closeService() {
  selectedService.value = null;
}

function serviceIcon(icon) {
  if (icon === "ambulance") return Ambulance;
  if (icon === "baby") return Baby;
  if (icon === "bed") return BedDouble;
  if (icon === "eye") return Eye;
  if (icon === "heart-pulse") return HeartPulse;
  if (icon === "medical-cross") return Cross;
  if (icon === "scissors") return Scissors;
  return Stethoscope;
}

function serviceIconLabel(details) {
  return details.iconLabel || "Doctor Consultation / Stethoscope";
}

function serviceSecondaryLabel(details) {
  if (details.serviceAvailability) return "សេវាកម្ម (Availability)";
  if (details.techniques) return "បច្ចេកវិទ្យាវះកាត់ (Techniques)";
  if (details.deliveryTypes) return "ជម្រើសសម្រាល (Delivery Types)";
  if (details.roomTypes) return "ប្រភេទបន្ទប់ (Room Types)";
  if (details.units) return "បន្ទប់ឯកទេស (Units)";
  if (details.hotline) return "ទូរស័ព្ទសង្គ្រោះបន្ទាន់ (Emergency Hotline)";
  return details.keyServices ? "សេវាកម្មចម្បង (Key Services)" : "ឯកទេស (Specialties)";
}

function serviceSecondaryValue(details) {
  if (details.serviceAvailability) return details.serviceAvailability;
  if (details.techniques) return details.techniques;
  if (details.deliveryTypes) return details.deliveryTypes;
  if (details.roomTypes) return details.roomTypes;
  if (details.units) return details.units;
  if (details.hotline) return details.hotline;
  return details.keyServices || details.specialties;
}

function servicePrimaryLabel(details) {
  if (details.departments) return "ផ្នែកឯកទេស (Departments)";
  if (details.operatingTheaters) return "បន្ទប់វះកាត់ (Operating Theaters)";
  if (details.coverage) return "សេវាកម្ម (Coverage)";
  if (details.careCoverage) return "សេវាកម្ម (Care Coverage)";
  return details.availability ? "សេវាកម្ម (Availability)" : "ម៉ោងបម្រើការ (Hours)";
}

function servicePrimaryValue(details) {
  if (details.departments) return details.departments;
  if (details.operatingTheaters) return details.operatingTheaters;
  if (details.coverage) return details.coverage;
  if (details.careCoverage) return details.careCoverage;
  return details.availability || details.hours;
}

function serviceActionIcon(details) {
  if (details.actionIcon === "baby") return Baby;
  if (details.actionIcon === "scissors") return Scissors;
  return details.actionIcon === "bed" ? BedDouble : CalendarDays;
}

function serviceAppointmentLabel(details) {
  return details.appointmentLabel || "កក់ការណាត់ជួប";
}

/* ── Post Gallery & Lightbox functions ── */
function formatPostGallery() {
  if (!postBodyRef.value) return;
  const container = postBodyRef.value;

  // Avoid re-formatting if already formatted
  if (container.querySelector(".post-gallery-grid")) return;

  const children = Array.from(container.children);
  let currentGallery = null;

  for (let i = 0; i < children.length; i++) {
    const el = children[i];

    // Skip Facebook iframe embeds
    if (
      el.classList.contains("facebook-post-embed") ||
      el.classList.contains("facebook-video-embed") ||
      el.classList.contains("fb-post-embed") ||
      el.querySelector("iframe")
    ) {
      currentGallery = null;
      continue;
    }

    // Check if element is directly an img
    if (el.tagName === "IMG") {
      if (!currentGallery) {
        currentGallery = document.createElement("div");
        currentGallery.className = "post-gallery-grid";
        container.insertBefore(currentGallery, el);
      }
      currentGallery.appendChild(el);
      continue;
    }

    // Check if element is a paragraph or div containing ONLY images (no real text)
    const imgs = Array.from(el.querySelectorAll("img"));
    if (imgs.length > 0) {
      const text = el.textContent.replace(/\u00a0/g, " ").trim();
      if (text.length === 0) {
        if (!currentGallery) {
          currentGallery = document.createElement("div");
          currentGallery.className = "post-gallery-grid";
          container.insertBefore(currentGallery, el);
        }
        imgs.forEach((img) => {
          img.removeAttribute("width");
          img.removeAttribute("height");
          currentGallery.appendChild(img);
        });
        el.remove();
        continue;
      }
    }

    // If it's an empty <p> or <br> between images, skip or remove if more images follow
    const textOnly = el.textContent.replace(/\u00a0/g, " ").trim();
    if (textOnly === "" && el.querySelectorAll("img, iframe").length === 0) {
      let nextHasImages = false;
      for (let j = i + 1; j < children.length; j++) {
        const next = children[j];
        if (
          next.tagName === "IMG" ||
          (next.querySelectorAll("img").length > 0 &&
            next.textContent.replace(/\u00a0/g, " ").trim() === "")
        ) {
          nextHasImages = true;
          break;
        }
        if (
          next.textContent.replace(/\u00a0/g, " ").trim().length > 0 ||
          next.querySelector("iframe")
        ) {
          break;
        }
      }
      if (nextHasImages && currentGallery) {
        el.remove();
        continue;
      }
    }

    // Normal text paragraph or heading resets current gallery
    currentGallery = null;
  }

  // Count items and add count-specific class
  container.querySelectorAll(".post-gallery-grid").forEach((grid) => {
    const totalImgs = grid.querySelectorAll("img").length;
    if (totalImgs === 1) {
      grid.classList.add("single-image");
    } else if (totalImgs === 2) {
      grid.classList.add("two-images");
    } else {
      grid.classList.add("multi-images");
    }
  });
}

function collectPostBodyImages() {
  if (!postBodyRef.value) return;
  formatPostGallery();
  const imgs = postBodyRef.value.querySelectorAll("img");
  const srcs = [];
  const hasHero = Boolean(postDetail.value?.post?.image);
  // Include hero image at index 0 if present
  if (hasHero) {
    srcs.push(postDetail.value.post.image);
  }
  // Collect body images with correct offset
  const offset = hasHero ? 1 : 0;
  imgs.forEach((img, i) => {
    srcs.push(img.src);
    img.style.cursor = "zoom-in";
    const idx = i + offset;
    img.onclick = (e) => {
      e.preventDefault();
      openLightbox(idx);
    };
  });
  lightboxImages.value = srcs;
}

function openLightbox(index) {
  lightboxIndex.value = index;
  lightboxOpen.value = true;
  document.body.style.overflow = "hidden";
}

function closeLightbox() {
  lightboxOpen.value = false;
  document.body.style.overflow = "";
}

function lightboxPrev() {
  if (lightboxIndex.value > 0) lightboxIndex.value--;
  else lightboxIndex.value = lightboxImages.value.length - 1;
}

function lightboxNext() {
  if (lightboxIndex.value < lightboxImages.value.length - 1) lightboxIndex.value++;
  else lightboxIndex.value = 0;
}

function onLightboxKeydown(e) {
  if (!lightboxOpen.value) return;
  if (e.key === "Escape") closeLightbox();
  if (e.key === "ArrowLeft") lightboxPrev();
  if (e.key === "ArrowRight") lightboxNext();
}

function onLightboxTouchStart(e) {
  touchStartX = e.touches[0].clientX;
  touchDeltaX = 0;
}

function onLightboxTouchMove(e) {
  touchDeltaX = e.touches[0].clientX - touchStartX;
}

function onLightboxTouchEnd() {
  if (Math.abs(touchDeltaX) > 50) {
    if (touchDeltaX > 0) lightboxPrev();
    else lightboxNext();
  }
  touchDeltaX = 0;
}

/* ── Post Sharing functions ── */
const postShareUrl = computed(() => {
  if (typeof window === "undefined") return "";
  const post = postDetail.value?.post;
  const isLocal = ["localhost", "127.0.0.1", "0.0.0.0"].includes(window.location.hostname);

  let baseOrigin = window.location.origin;
  const configuredPublic = site.value?.publicUrl || "https://dylan-syntax-checklist-paragraph.trycloudflare.com";
  if (isLocal && configuredPublic) {
    baseOrigin = configuredPublic.replace(/\/+$/, "");
  }

  if (!post) return `${baseOrigin}${window.location.pathname}`;
  return `${baseOrigin}/post/${post.id}`;
});

const shareFacebookUrl = computed(() => {
  const url = postShareUrl.value;
  const title = postDetail.value?.post?.title || "";
  const params = new URLSearchParams({ u: url });
  if (title) {
    params.set("quote", title);
  }
  return `https://www.facebook.com/sharer/sharer.php?${params.toString()}`;
});

const shareTelegramUrl = computed(() => {
  const title = postDetail.value?.post?.title || "";
  return `https://t.me/share/url?url=${encodeURIComponent(postShareUrl.value)}&text=${encodeURIComponent(title)}`;
});

const shareLinkedInUrl = computed(() => {
  return `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(postShareUrl.value)}`;
});

function openShare(url) {
  if (typeof window === "undefined" || !url) return;
  const width = 620;
  const height = 540;
  const left = Math.max(0, (window.innerWidth - width) / 2 + window.screenX);
  const top = Math.max(0, (window.innerHeight - height) / 2 + window.screenY);
  window.open(
    url,
    "_blank",
    `width=${width},height=${height},left=${left},top=${top},menubar=no,toolbar=no,status=no,resizable=yes`
  );
}

const showScrollTop = ref(false);

function onWindowScroll() {
  showScrollTop.value = window.scrollY > 250;
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function submitAppointment() {
  appointmentLoading.value = true;
  appointmentStatus.value = null;
  try {
    const token = await ensureCsrfToken();
    const data = await fetchJson("/api/appointments", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": token,
      },
      body: JSON.stringify(form),
    });
    appointmentStatus.value = { type: "success", text: data.notice || data.message };
    Object.assign(form, {
      name: "",
      phone: "",
      email: "",
      reason: "",
      department: "Outpatient Care",
      datetime: "",
    });
  } catch (error) {
    appointmentStatus.value = { type: "error", text: "Please check the form and try again." };
  } finally {
    appointmentLoading.value = false;
  }
}

watch(
  () => route.fullPath,
  () => {
    searchText.value = route.query.q || "";
    menuOpen.value = false;
    loadAll();
  }
);

let visitorPollTimer = null;

async function trackVisitor() {
  const sessionKey = "kcnprh_visitor_session";
  const hasVisited = typeof sessionStorage !== "undefined" ? sessionStorage.getItem(sessionKey) : null;
  try {
    if (!hasVisited) {
      if (typeof sessionStorage !== "undefined") {
        sessionStorage.setItem(sessionKey, "1");
      }
      const res = await fetchJson("/api/track-visit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (res?.visitorCount) {
        visitorCount.value = res.visitorCount;
        return;
      }
    } else {
      const res = await fetchJson("/api/visitor-count");
      if (res?.visitorCount) {
        visitorCount.value = res.visitorCount;
        return;
      }
    }
  } catch (e) {
    // Keep current visitorCount on failure
  }
}

async function refreshVisitorCount() {
  try {
    const res = await fetchJson("/api/visitor-count");
    if (res?.visitorCount) {
      visitorCount.value = res.visitorCount;
    }
  } catch (e) {}
}

onMounted(() => {
  loadAll();
  trackVisitor();
  if (typeof window !== "undefined") {
    visitorPollTimer = setInterval(refreshVisitorCount, 30000);
  }
  document.addEventListener("keydown", onLightboxKeydown);
  window.addEventListener("scroll", onWindowScroll, { passive: true });
});

onUnmounted(() => {
  if (visitorPollTimer) clearInterval(visitorPollTimer);
  document.removeEventListener("keydown", onLightboxKeydown);
  window.removeEventListener("scroll", onWindowScroll);
});

// Wire up document head and lightbox click handlers after post body renders
watch(
  () => postDetail.value,
  () => {
    if (postDetail.value?.post) {
      const p = postDetail.value.post;
      if (typeof document !== "undefined") {
        const siteName = site.value?.khmerName || "មន្ទីរពេទ្យខេត្តកំពង់ឆ្នាំង";
        document.title = p.title ? `${p.title} | ${siteName}` : siteName;

        const updateMeta = (attr, key, val) => {
          if (!val) return;
          let el = document.querySelector(`meta[${attr}="${key}"]`);
          if (!el) {
            el = document.createElement("meta");
            el.setAttribute(attr, key);
            document.head.appendChild(el);
          }
          el.setAttribute("content", val);
        };

        updateMeta("property", "og:title", p.title);
        if (p.excerpt) updateMeta("property", "og:description", p.excerpt);
        if (p.image) updateMeta("property", "og:image", p.image);
        updateMeta("property", "og:url", window.location.href);
      }
      nextTick(() => {
        setTimeout(collectPostBodyImages, 100);
      });
    }
  }
);
</script>

<template>
  <div class="site-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/">
        <img v-if="site?.logo" :src="site.logo" alt="" />
        <span>
          <strong>{{ site?.khmerName || "មន្ទីរពេទ្យខេត្តកំពង់ឆ្នាំង" }}</strong>
          <small>{{ site?.name || "Kampong Chhnang Provincial Referral Hospital" }}</small>
        </span>
      </RouterLink>

      <nav :class="{ open: menuOpen }" class="nav">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/news">News</RouterLink>
        <RouterLink to="/about">About</RouterLink>
        <RouterLink to="/contact">Contact</RouterLink>
        <a href="/admin">Admin</a>
        <form v-if="searchEnabled" class="mobile-search" @submit.prevent="goSearch">
          <Search :size="18" />
          <input v-model="searchText" type="search" placeholder="Search news" />
        </form>
      </nav>

      <form v-if="searchEnabled" class="searchbar" @submit.prevent="goSearch">
        <Search :size="18" />
        <input v-model="searchText" type="search" placeholder="Search news" />
      </form>

      <button class="icon-button menu-button" type="button" aria-label="Menu" @click="menuOpen = !menuOpen">
        <X v-if="menuOpen" :size="22" />
        <Menu v-else :size="22" />
      </button>
</header>

    <div v-if="isNavigating" class="top-progress-bar" role="progressbar" aria-label="Loading">
      <div class="top-progress-bar-indicator"></div>
    </div>

    <main class="main-content">
      <section v-if="isLanding" class="hero">
        <img v-if="site?.heroImage" :src="site.heroImage" alt="" fetchpriority="high" decoding="async" />
        <div class="hero-shade"></div>
        <div class="hero-content">
          <p class="eyebrow"><ShieldCheck :size="18" /> Public Provincial Hospital</p>
          <h1>{{ site?.khmerName }}</h1>
          <p>{{ site?.tagline }}</p>
          <div class="hero-actions">
            <RouterLink class="primary-action" to="/contact"><CalendarDays :size="19" /> Book Appointment</RouterLink>
            <a class="secondary-action" href="tel:0979812812"><Ambulance :size="19" /> Emergency Call</a>
          </div>
        </div>
        <div class="hero-stats">
          <div v-for="item in site?.stats" :key="item.label">
            <strong>{{ item.value }}</strong>
            <span>{{ item.label }}</span>
          </div>
        </div>
      </section>

      <section v-if="isLanding && emergencyServices.length" class="section emergency-services-section">
        <div class="section-heading">
          <p class="eyebrow"><Ambulance :size="18" /> 24/7 Care</p>
          <h2>សេវាបន្ទាន់ ២៤ម៉ោង</h2>
          <span class="section-subtitle">24/7 Emergency Services for ambulance transfer, emergency treatment, and inpatient monitoring.</span>
        </div>
        <div class="emergency-service-grid">
          <RouterLink
            v-for="service in emergencyServices"
            :key="service.title"
            class="emergency-service-card"
            :to="servicePath(service)"
          >
            <div class="emergency-service-image-wrap">
              <img :src="service.image" :alt="service.title" loading="lazy" decoding="async" />
              <span class="emergency-service-badge">
                <component :is="serviceIcon(service.details.icon)" :size="18" />
              </span>
            </div>
            <div class="emergency-service-content">
              <strong>{{ service.khmer }}</strong>
              <span>{{ service.title }}</span>
              <p>{{ service.details.description }}</p>
              <span class="emergency-service-link">
                ស្វែងយល់បន្ថែម <ArrowRight :size="15" />
              </span>
            </div>
          </RouterLink>
        </div>
      </section>

      <section v-if="isLanding" class="section services-section">
        <div class="section-heading">
          <p class="eyebrow"><Stethoscope :size="18" /> Care Services</p>
          <h2>សេវាសុខភាព</h2>
          <span class="section-subtitle">Fast access to the main hospital services patients need most.</span>
        </div>
        <div class="service-grid">
          <article v-for="service in regularServices" :key="service.title" class="service-card">
            <div class="service-card-image-wrap">
              <img :src="service.image" :alt="service.title" loading="lazy" decoding="async" />
            </div>
            <div class="service-card-content">
              <strong>{{ service.khmer }}</strong>
              <span>{{ service.title }}</span>
              <RouterLink v-if="service.details" class="service-card-link" :to="servicePath(service)">
                ស្វែងយល់បន្ថែម <ArrowRight :size="15" />
              </RouterLink>
            </div>
          </article>
        </div>
      </section>

      <Transition name="modal-bounce">
        <div v-if="selectedService?.details" class="service-modal-backdrop" @click.self="closeService">
          <section class="service-modal" role="dialog" aria-modal="true" aria-labelledby="service-modal-title">
            <button class="service-modal-close" type="button" aria-label="Close" @click="closeService">
              <X :size="21" />
            </button>
            <div class="service-modal-icon">
              <component :is="serviceIcon(selectedService.details.icon)" :size="34" />
            </div>
            <div>
              <p class="eyebrow">{{ serviceIconLabel(selectedService.details) }}</p>
              <h2 id="service-modal-title">{{ selectedService.details.title }}</h2>
              <h3>{{ selectedService.details.subtitle }}</h3>
              <p class="service-modal-khmer">{{ selectedService.details.description }}</p>
              <p class="service-modal-english">{{ selectedService.details.english }}</p>
              <div class="service-info-grid">
                <div>
                  <strong>{{ servicePrimaryLabel(selectedService.details) }}</strong>
                  <span>{{ servicePrimaryValue(selectedService.details) }}</span>
                </div>
                <div>
                  <strong>{{ serviceSecondaryLabel(selectedService.details) }}</strong>
                  <span>{{ serviceSecondaryValue(selectedService.details) }}</span>
                </div>
              </div>
              <div class="service-modal-actions">
                <template v-if="selectedService.details.callNow">
                  <a class="primary-action emergency-call-action" :href="phoneHref(selectedService.details.callNow)">
                    <Phone :size="18" /> {{ selectedService.details.callLabel }}
                  </a>
                  <a class="secondary-detail-action" href="#services" @click.prevent="closeService">
                    {{ selectedService.details.learnMoreLabel || "ស្វែងយល់បន្ថែម" }}
                  </a>
                </template>
                <template v-else>
                  <a class="secondary-detail-action" href="#services" @click.prevent="closeService">
                    {{ selectedService.details.learnMoreLabel || "ស្វែងយល់បន្ថែម" }}
                  </a>
                  <RouterLink class="primary-action" to="/contact" @click="closeService">
                    <component :is="serviceActionIcon(selectedService.details)" :size="18" />
                    {{ serviceAppointmentLabel(selectedService.details) }}
                  </RouterLink>
                </template>
              </div>
            </div>
          </section>
        </div>
      </Transition>

      <section v-if="pathMode === 'home' || pathMode === 'news'" class="section news-layout">
        <div class="content-column">
          <RouterLink v-if="!isLanding" class="back-link" to="/"><ArrowLeft :size="18" /> Back to Home</RouterLink>
          <div class="section-heading">
            <p class="eyebrow"><Newspaper :size="18" /> Hospital Updates</p>
            <h2>{{ updatesHeading }}</h2>
            <span class="section-subtitle">Latest hospital announcements, health education, and public service notices.</span>
          </div>
          <div v-if="categoryPillsEnabled && !isLanding && postsData.categories.length" class="news-category-pills">
            <RouterLink class="category-pill" :class="{ active: !categoryId && !route.query.q }" to="/news">
              All Updates
            </RouterLink>
            <RouterLink
              v-for="cat in postsData.categories"
              :key="cat.id"
              class="category-pill"
              :class="{ active: categoryId === cat.id }"
              :to="`/category/${cat.id}`"
            >
              {{ cat.name }}
            </RouterLink>
          </div>

          <div v-if="isLanding" class="updates-overview">
            <div class="updates-notice">
              <ShieldCheck :size="18" />
              <span>Verified updates from Kampong Chhnang Provincial Referral Hospital for patients, families, and visitors.</span>
            </div>
            <div class="updates-mini-stats" aria-label="Hospital update summary">
              <span><strong>{{ postsData.posts.length + 1 }}</strong> Updates</span>
              <span><Clock3 :size="15" /> Latest first</span>
            </div>
          </div>
          <article v-if="isLanding" class="nssf-update-card">
            <div class="nssf-update-banner">
              <span class="news-pill">Hospital Update</span>
              <time>{{ aimNssfUpdate.date }}</time>
            </div>
            <div class="nssf-update-body">
              <div class="nssf-update-icon">
                <ShieldCheck :size="34" />
              </div>
              <div class="nssf-update-copy">
                <h3>{{ aimNssfUpdate.title }}</h3>
                <p>{{ aimNssfUpdate.subtitle }}</p>
                <div class="nssf-update-details">
                  <span><CheckCircle2 :size="16" /> {{ aimNssfUpdate.status }}</span>
                  <span><MapPin :size="16" /> {{ aimNssfUpdate.location }}</span>
                  <span><Clock3 :size="16" /> Faster patient check-in</span>
                </div>
                <button class="nssf-update-link" type="button" @click="aimNssfOpen = true">
                  Read full update <ArrowRight :size="15" />
                </button>
              </div>
            </div>
          </article>
          <Transition name="modal-bounce">
            <div v-if="aimNssfOpen" class="nssf-update-modal-backdrop" @click.self="aimNssfOpen = false">
              <section class="nssf-update-modal" role="dialog" aria-modal="true" aria-labelledby="aim-nssf-title">
                <button class="nssf-update-close" type="button" aria-label="Close update" @click="aimNssfOpen = false">
                  <X :size="21" />
                </button>
                <div class="nssf-update-modal-header">
                  <span class="news-pill">AIM NSSF</span>
                  <time>{{ aimNssfUpdate.date }}</time>
                </div>
                <h2 id="aim-nssf-title">{{ aimNssfUpdate.title }}</h2>
                <p class="nssf-update-subtitle">{{ aimNssfUpdate.subtitle }}</p>

                <div class="nssf-update-status-grid">
                  <div>
                    <CheckCircle2 :size="19" />
                    <span>Status</span>
                    <strong>{{ aimNssfUpdate.status }}</strong>
                  </div>
                  <div>
                    <MapPin :size="19" />
                    <span>Location</span>
                    <strong>{{ aimNssfUpdate.location }}</strong>
                  </div>
                </div>

                <div class="nssf-guide-section">
                  <h3>{{ aimNssfUpdate.stepsTitle }}</h3>
                  <div class="nssf-step-grid">
                    <article v-for="(step, index) in aimNssfUpdate.steps" :key="step.title">
                      <span>{{ index + 1 }}</span>
                      <h4>{{ step.title }}</h4>
                      <p>{{ step.desc }}</p>
                    </article>
                  </div>
                </div>

                <div class="nssf-guide-section">
                  <h3>{{ aimNssfUpdate.benefitsTitle }}</h3>
                  <ul class="nssf-benefit-list">
                    <li v-for="benefit in aimNssfUpdate.benefits" :key="benefit">
                      <CheckCircle2 :size="17" />
                      <span>{{ benefit }}</span>
                    </li>
                  </ul>
                </div>

                <div class="nssf-guide-notes">
                  <p v-for="note in aimNssfUpdate.notes" :key="note">{{ note }}</p>
                </div>
              </section>
            </div>
          </Transition>
          <div v-if="featuredPost" class="featured-grid">
            <RouterLink class="featured-card" :to="featuredPost.url">
              <div class="featured-media">
                <img v-if="featuredPost.image" :src="featuredPost.image" :alt="featuredPost.title" loading="lazy" decoding="async" />
                <div v-else class="image-fallback">
                  <Newspaper :size="42" />
                </div>
              </div>
              <div class="featured-copy">
                <div class="featured-meta-row">
                  <span class="news-pill">Featured Update</span>
                  <time>{{ featuredPost.date || "Hospital News" }}</time>
                </div>
                <h3>{{ featuredPost.title }}</h3>
                <p>{{ featuredPost.excerpt || "Read the latest update from the hospital." }}</p>
                <small class="post-read-more">Read full update <ArrowRight :size="15" /></small>
              </div>
            </RouterLink>
          </div>
          <div class="post-grid">
            <div v-if="pathMode === 'news' && facebookFeedEnabled" class="post-card facebook-card-item">
              <div class="fb-card-top">
                <div class="post-card-meta">
                  <span class="fb-card-pill"><Facebook :size="13" /> Facebook Updates</span>
                  <time>Real-Time</time>
                </div>
                <a :href="contact.facebook || 'https://www.facebook.com/profile.php?id=100068634422929'" target="_blank" rel="noopener">
                  View Page <ArrowRight :size="13" />
                </a>
              </div>
              <div class="fb-card-frame-wrap">
                <iframe
                  title="Latest Facebook posts"
                  :src="`https://www.facebook.com/plugins/page.php?href=${encodeURIComponent(contact.facebook || 'https://www.facebook.com/profile.php?id=100068634422929')}&tabs=timeline&width=500&height=480&small_header=true&adapt_container_width=true&hide_cover=false&show_facepile=false`"
                  width="100%"
                  height="100%"
                  style="border: none; overflow: hidden; width: 100%; height: 100%; min-height: 440px;"
                  scrolling="no"
                  frameborder="0"
                  allowfullscreen="true"
                  allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
                ></iframe>
              </div>
            </div>

            <RouterLink v-for="post in updatePosts" :key="post.id" class="post-card" :to="post.url">
              <div class="post-card-media">
                <img v-if="post.image" :src="post.image" :alt="post.title" loading="lazy" decoding="async" />
                <div v-else class="image-fallback compact">
                  <Newspaper :size="28" />
                </div>
              </div>
              <div class="post-card-body">
                <div class="post-card-meta">
                  <span class="news-pill">{{ post.category?.name || "Announcement" }}</span>
                  <time>{{ post.date || "Hospital Update" }}</time>
                </div>
                <h3>{{ post.title }}</h3>
                <p>{{ post.excerpt || "Read the latest update from the hospital." }}</p>
                <small class="post-read-more">Read More <ArrowRight :size="15" /></small>
              </div>
            </RouterLink>
            <div v-if="!postsData.posts.length" class="empty-state">
              <Newspaper :size="34" />
              <strong>No posts yet</strong>
              <span>News will appear here after content is added in the admin panel.</span>
            </div>
          </div>
          <!-- Home page limit: See more button -->
          <div v-if="isLanding" class="see-more-posts-wrap">
            <RouterLink class="see-more-posts-btn" to="/news">
              <span>មើលព័ត៌មានទាំងអស់ ({{ postsData.pagination.total || postsData.posts.length }}) · View More Updates</span>
              <ArrowRight :size="18" />
            </RouterLink>
          </div>

          <!-- Dedicated News page: Full pagination -->
          <div v-if="!isLanding && postsData.pagination.pages > 1" class="pager">
            <button :disabled="!postsData.pagination.hasPrev" @click="setPage(postsData.pagination.page - 1)">
              <ArrowLeft :size="18" /> Prev
            </button>
            <span>{{ postsData.pagination.page }} / {{ postsData.pagination.pages }}</span>
            <button :disabled="!postsData.pagination.hasNext" @click="setPage(postsData.pagination.page + 1)">
              Next <ArrowRight :size="18" />
            </button>
          </div>
        </div>

      </section>

      <section v-if="isLanding" class="section emergency-section">
        <aside class="hero-emergency-card">
          <p><Ambulance :size="20" /> Emergency Hotline</p>
          <a v-for="phone in site?.emergencyPhones" :key="phone" :href="phoneHref(phone)">
            <Phone :size="18" /> {{ phone }}
          </a>
          <span><Clock3 :size="17" /> Open 24 hours, every day</span>
        </aside>
      </section>

      <section v-if="pathMode === 'service' && activeService?.details" class="section service-page">
        <RouterLink class="back-link" to="/"><ArrowLeft :size="18" /> Back to services</RouterLink>
        <div class="service-page-hero">
          <div class="service-page-image">
            <img :src="activeService.image" :alt="activeService.title" loading="lazy" decoding="async" />
          </div>
          <div class="service-page-copy">
            <p class="eyebrow">{{ serviceIconLabel(activeService.details) }}</p>
            <h1>{{ activeService.details.title }}</h1>
            <h2>{{ activeService.details.subtitle }}</h2>
            <p>{{ activeService.details.description }}</p>
            <p class="service-page-english">{{ activeService.details.english }}</p>
          </div>
        </div>

        <div v-if="activeService.details.consultations" class="service-detail-list service-page-list">
          <article v-for="item in activeService.details.consultations" :key="item.title">
            <CheckCircle2 :size="18" />
            <div>
              <h4>{{ item.title }}</h4>
              <p>{{ item.description }}</p>
            </div>
          </article>
        </div>

        <div class="service-info-grid service-page-info">
          <div>
            <strong>{{ servicePrimaryLabel(activeService.details) }}</strong>
            <span>{{ servicePrimaryValue(activeService.details) }}</span>
          </div>
          <div>
            <strong>{{ serviceSecondaryLabel(activeService.details) }}</strong>
            <span>{{ serviceSecondaryValue(activeService.details) }}</span>
          </div>
        </div>

        <div class="service-modal-actions">
          <template v-if="activeService.details.callNow">
            <a class="primary-action emergency-call-action" :href="phoneHref(activeService.details.callNow)">
              <Phone :size="18" /> {{ activeService.details.callLabel }}
            </a>
          </template>
          <RouterLink class="primary-action" to="/contact">
            <component :is="serviceActionIcon(activeService.details)" :size="18" />
            {{ serviceAppointmentLabel(activeService.details) }}
          </RouterLink>
        </div>
      </section>

      <section v-else-if="pathMode === 'service'" class="section static-page">
        <RouterLink class="back-link" to="/"><ArrowLeft :size="18" /> Back to services</RouterLink>
        <h1>Service not found</h1>
        <article>This service page is not available.</article>
      </section>

      <section v-if="pathMode === 'about'" class="section about-page">
        <div class="section-heading">
          <p class="eyebrow"><ShieldCheck :size="18" /> Leadership</p>
          <h1>រចនាសម្ពន្ធ័</h1>
        </div>
        <div v-if="director" class="leaders-top-row">
          <article class="leader-card">
            <img :src="director.image" :alt="director.name" loading="lazy" decoding="async" />
            <strong>{{ director.khmer }}</strong>
            <span>{{ director.name }}</span>
            <small>{{ director.role }}</small>
          </article>
        </div>
        <div class="leaders-grid">
          <article v-for="leader in viceLeaders" :key="leader.name" class="leader-card">
            <img :src="leader.image" :alt="leader.name" loading="lazy" decoding="async" />
            <strong>{{ leader.khmer }}</strong>
            <span>{{ leader.name }}</span>
            <small>{{ leader.role }}</small>
          </article>
        </div>
        <div class="mission-grid">
          <article>
            <h2>បេសកកម្ម</h2>
            <p>មន្ទីរពេទ្យខេត្តកំពង់ឆ្នាំង ផ្តល់សេវាសុខភាពប្រកបដោយគុណភាព និងសុវត្ថិភាពស្របតាមស្តង់ដារនៃការទទួលស្គាល់គុណភាពមន្ទីរពេទ្យ។</p>
          </article>
          <article>
            <h2>ចក្ខុវិស័យ</h2>
            <p>ក្លាយជាមន្ទីរពេទ្យផ្តល់សេវាសុខភាពស្របតាមស្តង់ដារនៃការទទួលស្គាល់គុណភាពមន្ទីរពេទ្យនៅកម្ពុជា។</p>
          </article>
          <article>
            <h2>គុណតម្លៃ</h2>
            <p>ក្រមសីលធម៌វិជ្ជាជីវៈ តម្លាភាព ការប្តេជ្ញាចិត្ត សមធម៌ និងការបើកចិត្តទូលាយ។</p>
          </article>
        </div>
      </section>

      <section v-if="pathMode === 'contact'" class="section contact-page">
        <div class="contact-header">
          <div class="section-heading">
            <p class="eyebrow"><Phone :size="18" /> Contact</p>
            <h1>ទំនាក់ទំនង និងការណាត់ជួប</h1>
            <span class="section-subtitle">Fast contact options, appointment requests, and visit information for patients and families.</span>
          </div>
          <div class="quick-contact">
            <a class="quick-contact-item emergency" :href="phoneHref(site?.emergencyPhones?.[0] || contact.phones?.[0] || '')">
              <Phone :size="20" />
              <span>Emergency Call</span>
              <strong>{{ site?.emergencyPhones?.[0] || contact.phones?.[0] }}</strong>
            </a>
            <a class="quick-contact-item" :href="phoneHref(contact.phones?.[0] || '')">
              <Phone :size="20" />
              <span>General Phone</span>
              <strong>{{ contact.phones?.[0] }}</strong>
            </a>
            <a class="quick-contact-item" :href="contact.facebook" target="_blank" rel="noopener">
              <Facebook :size="20" />
              <span>Facebook</span>
              <strong>Message us</strong>
            </a>
            <a class="quick-contact-item" :href="contact.map" target="_blank" rel="noopener">
              <MapPin :size="20" />
              <span>Google Map</span>
              <strong>Get directions</strong>
            </a>
          </div>
        </div>

        <div class="contact-main-grid">
        <div class="appointment-panel">
          <div class="section-heading">
            <p class="eyebrow"><CalendarDays :size="18" /> Appointment</p>
            <h2>ការណាត់ជួប</h2>
          </div>
          <form class="appointment-form" @submit.prevent="submitAppointment">
            <label><span>ឈ្មោះ (Name)</span><input v-model="form.name" required type="text" /></label>
            <label><span>លេខទូរស័ព្ទ (Phone)</span><input v-model="form.phone" required type="tel" /></label>
            <label><span>អ៊ីមែល (Email)</span><input v-model="form.email" type="email" /></label>
            <label>
              <span>ផ្នែកសេវាកម្ម (Department)</span>
              <select v-model="form.department">
                <option>Outpatient Care</option>
                <option>Eye Care & Ophthalmology</option>
                <option>Ear, Nose & Throat (ENT)</option>
                <option>Pediatric & Neonatal Care</option>
                <option>Hemodialysis Service</option>
                <option>Emergency Ambulance 24/7</option>
                <option>Emergency & ICU</option>
                <option>Inpatient Care / IPD</option>
                <option>Maternity & Delivery Care</option>
                <option>Surgery & Operating Theater</option>
                <option>More Services & Specialties</option>
              </select>
            </label>
            <label><span>ថ្ងៃ និងម៉ោង (Date & Time)</span><input v-model="form.datetime" required type="datetime-local" /></label>
            <label class="form-wide"><span>មូលហេតុ / សារ (Reason / Message)</span><textarea v-model="form.reason" required rows="5"></textarea></label>
            <button class="primary-action" type="submit" :disabled="appointmentLoading">
              <Send :size="18" /> {{ appointmentLoading ? "Sending..." : "Submit" }}
            </button>
            <p v-if="appointmentStatus" :class="['form-status', appointmentStatus.type]">
              <CheckCircle2 v-if="appointmentStatus.type === 'success'" :size="18" />
              {{ appointmentStatus.text }}
            </p>
          </form>
        </div>

        <aside class="contact-side">
          <div class="contact-panel">
            <img :src="site?.heroImage" alt="" loading="lazy" decoding="async" />
            <div class="contact-list">
              <a :href="contact.map" target="_blank" rel="noopener"><MapPin :size="19" /> {{ contact.address }}</a>
              <a :href="`mailto:${contact.email}`"><Mail :size="19" /> {{ contact.email }}</a>
              <a v-for="phone in contact.phones" :key="phone" :href="phoneHref(phone)"><Phone :size="19" /> {{ phone }}</a>
              <span><Clock3 :size="19" /> {{ contact.hours }}</span>
              <a :href="contact.facebook" target="_blank" rel="noopener"><Facebook :size="19" /> Facebook</a>
            </div>
          </div>

          <div class="visit-panel">
            <h3>Visit Information</h3>
            <p><Clock3 :size="18" /> Open 24/7 for emergency and inpatient care.</p>
            <p><ShieldCheck :size="18" /> Bring ID, health records, and current medicine list if available.</p>
            <p><MapPin :size="18" /> Use Google Map for the fastest route to the hospital entrance.</p>
          </div>

          <div class="next-steps-panel">
            <h3>What happens next?</h3>
            <ol>
              <li>Submit request</li>
              <li>Staff review</li>
              <li>Phone confirmation</li>
              <li>Visit hospital</li>
            </ol>
          </div>
        </aside>
        </div>
      </section>

      <section v-if="pathMode === 'post' && postDetail?.post" class="section post-detail">
        <RouterLink class="back-link" to="/news"><ArrowLeft :size="18" /> Back to news</RouterLink>
        <div v-if="postDetail.post.image" class="post-detail-hero" @click="openLightbox(0)" style="cursor: zoom-in;">
          <img :src="postDetail.post.image" :alt="postDetail.post.title" loading="eager" decoding="async" />
          <div class="post-detail-hero-overlay"></div>
          <div class="post-detail-hero-content">
            <span class="news-pill">{{ postDetail.post.category?.name || "News" }}</span>
          </div>
        </div>
        <div class="post-detail-header">
          <p v-if="!postDetail.post.image" class="eyebrow"><Newspaper :size="18" /> {{ postDetail.post.category?.name || "News" }}</p>
          <h1>{{ postDetail.post.title }}</h1>
          <div class="post-detail-meta-row">
            <div class="post-detail-meta-info">
              <span class="post-detail-date"><CalendarDays :size="15" /> {{ postDetail.post.date }}</span>
              <span class="post-detail-views"><Eye :size="15" /> {{ postDetail.post.views }} views</span>
            </div>
          </div>
        </div>
        <div v-if="isAimNssfPost" class="aim-post-action-panel">
          <div>
            <strong>{{ aimNssfUpdate.stepsTitle }}</strong>
            <span>{{ aimNssfUpdate.status }} · {{ aimNssfUpdate.location }}</span>
          </div>
          <button class="aim-checklist-button" type="button" @click="aimNssfChecklistOpen = true">
            <CheckCircle2 :size="18" /> បើកបញ្ជីឯកសារត្រូវត្រៀម
          </button>
        </div>
        <Transition name="modal-bounce">
          <div v-if="isAimNssfPost && aimNssfChecklistOpen" class="aim-checklist-backdrop" @click.self="aimNssfChecklistOpen = false">
            <section class="aim-checklist-modal" role="dialog" aria-modal="true" aria-labelledby="aim-checklist-title">
              <div class="aim-checklist-header">
                <div>
                  <span>[ ✓ ]</span>
                  <h2 id="aim-checklist-title">ឯកសារចាំបាច់ត្រូវយកមកជាមួយ</h2>
                </div>
                <button type="button" aria-label="Close checklist" @click="aimNssfChecklistOpen = false">[ × ]</button>
              </div>
              <p class="aim-checklist-intro">
                សូមរៀបចំឯកសារខាងក្រោមមុនពេលមកដល់ច្រកចុះឈ្មោះ ដើម្បីផ្ទៀងផ្ទាត់ ប.ស.ស។
              </p>
              <div class="aim-checklist-progress">
                <strong>{{ aimNssfReadyCount }} / {{ aimNssfDocuments.length }}</strong>
                <span>បានត្រៀមរួច</span>
              </div>
              <label v-for="document in aimNssfDocuments" :key="document.title" class="aim-document-row">
                <input v-model="document.checked" type="checkbox" />
                <div>
                  <strong>{{ document.title }}</strong>
                  <span>{{ document.desc }}</span>
                </div>
              </label>
              <div class="aim-checklist-footer">
                <button class="aim-checklist-confirm" type="button" @click="aimNssfChecklistOpen = false">
                  យល់ព្រម
                </button>
              </div>
            </section>
          </div>
        </Transition>
        <article ref="postBodyRef" class="post-body" v-html="postDetail.post.body"></article>

        <!-- Post Footer Share Section -->
        <div class="post-detail-share-footer">
          <div class="post-share-buttons">
            <a
              :href="shareFacebookUrl"
              class="share-btn share-btn-fb"
              target="_blank"
              rel="noopener noreferrer"
              title="Share to Facebook"
              @click.prevent="openShare(shareFacebookUrl)"
            >
              <span>ចែករំលែក</span>
              <svg class="share-icon" viewBox="0 0 24 24" fill="currentColor" width="13" height="13">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
              </svg>
            </a>
            <a
              :href="shareTelegramUrl"
              class="share-btn share-btn-tg"
              target="_blank"
              rel="noopener noreferrer"
              title="Share to Telegram"
              @click.prevent="openShare(shareTelegramUrl)"
            >
              <span>ចែករំលែក</span>
              <svg class="share-icon" viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </a>
          </div>
        </div>
      </section>

      <section v-else-if="pathMode === 'post' && isNavigating" class="section post-detail skeleton-view">
        <div class="skeleton-line short"></div>
        <div class="skeleton-block"></div>
        <div class="skeleton-line medium"></div>
        <div class="skeleton-line long"></div>
      </section>

      <section v-else-if="pathMode === 'post'" class="section static-page">
        <RouterLink class="back-link" to="/"><ArrowLeft :size="18" /> Back to news</RouterLink>
        <h1>Post not found</h1>
        <article>This news article is not available.</article>
      </section>

      <!-- Facebook-style Image Lightbox (fixed overlay) -->
      <Transition name="lightbox-fade">
        <div
          v-if="lightboxOpen && lightboxImages.length"
          class="lightbox-backdrop"
          @click.self="closeLightbox"
          @touchstart.passive="onLightboxTouchStart"
          @touchmove.passive="onLightboxTouchMove"
          @touchend="onLightboxTouchEnd"
        >
          <button class="lightbox-close" type="button" aria-label="Close" @click="closeLightbox">
            <X :size="24" />
          </button>

          <button
            v-if="lightboxImages.length > 1"
            class="lightbox-arrow lightbox-arrow-left"
            type="button"
            aria-label="Previous image"
            @click="lightboxPrev"
          >
            <ArrowLeft :size="28" />
          </button>

          <div class="lightbox-image-wrap">
            <Transition name="lightbox-slide" mode="out-in">
              <img
                :key="lightboxIndex"
                :src="lightboxImages[lightboxIndex]"
                alt=""
                class="lightbox-image"
                @click.stop
              />
            </Transition>
          </div>

          <button
            v-if="lightboxImages.length > 1"
            class="lightbox-arrow lightbox-arrow-right"
            type="button"
            aria-label="Next image"
            @click="lightboxNext"
          >
            <ArrowRight :size="28" />
          </button>

          <div v-if="lightboxImages.length > 1" class="lightbox-counter">
            {{ lightboxIndex + 1 }} / {{ lightboxImages.length }}
          </div>

          <div v-if="lightboxImages.length > 1" class="lightbox-dots">
            <button
              v-for="(img, i) in lightboxImages"
              :key="i"
              :class="['lightbox-dot', { active: i === lightboxIndex }]"
              type="button"
              :aria-label="`Go to image ${i + 1}`"
              @click="lightboxIndex = i"
            ></button>
          </div>
        </div>
      </Transition>

      <section v-if="pathMode === 'page'" class="section static-page">
        <h1>{{ pageDetail?.title || "Page not found" }}</h1>
        <article v-if="pageDetail" v-html="pageDetail.body"></article>
      </section>
    </main>

    <footer class="moh-footer">
      <div class="moh-footer-container">
        <!-- Column 1: Hospital Name & Contact Info -->
        <div class="moh-footer-col moh-col-identity">
          <h3 class="moh-footer-title">{{ site?.khmerName || "មន្ទីរពេទ្យបង្អែកខេត្តកំពង់ឆ្នាំង" }}</h3>
          <p class="moh-footer-address">{{ contact?.address || "ភូមិទី១ សង្កាត់កំពង់ឆ្នាំង ក្រុងកំពង់ឆ្នាំង ខេត្តកំពង់ឆ្នាំង" }}</p>
          <div class="moh-footer-contact-item">
            <strong>Hotlines:</strong>
            <a :href="`tel:${(contact?.phones?.[0] || '0979812812').replace(/\s+/g, '')}`">{{ contact?.phones?.[0] || "097 981 2812" }}</a>
            <span v-if="contact?.phones?.[1]"> / </span>
            <a v-if="contact?.phones?.[1]" :href="`tel:${contact.phones[1].replace(/\s+/g, '')}`">{{ contact.phones[1] }}</a>
          </div>
          <div class="moh-footer-contact-item">
            <strong>Email:</strong>
            <a :href="`mailto:${contact?.email || 'kcnprh@gmail.com'}`">{{ contact?.email || "kcnprh@gmail.com" }}</a>
          </div>
        </div>

        <!-- Column 2: អំពីមន្ទីរពេទ្យ (About) -->
        <div class="moh-footer-col">
          <h3 class="moh-footer-title">អំពីមន្ទីរពេទ្យ</h3>
          <ul class="moh-footer-links">
            <li>
              <RouterLink to="/about">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
                <span>ថ្នាក់ដឹកនាំ</span>
              </RouterLink>
            </li>
            <li>
              <RouterLink to="/about">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg>
                <span>រចនាសម្ព័ន្ធ</span>
              </RouterLink>
            </li>
            <li>
              <RouterLink to="/about">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                <span>បេសកកម្ម និងចក្ខុវិស័យ</span>
              </RouterLink>
            </li>
          </ul>
        </div>

        <!-- Column 3: ព័ត៌មាន និងសេវាកម្ម (News & Services) -->
        <div class="moh-footer-col">
          <h3 class="moh-footer-title">ព័ត៌មាន និងសេវាកម្ម</h3>
          <ul class="moh-footer-links">
            <li>
              <RouterLink to="/news">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"/></svg>
                <span>ព័ត៌មាន និងសេចក្តីជូនដំណឹង</span>
              </RouterLink>
            </li>
            <li>
              <RouterLink to="/contact">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V9h14v10zm-7-7h5v5h-5z"/></svg>
                <span>ទំនាក់ទំនង និងការណាត់ជួប</span>
              </RouterLink>
            </li>
          </ul>
        </div>

        <!-- Column 4: បណ្តាញសង្គម (Social Networks & Visitor Count) -->
        <div class="moh-footer-col">
          <h3 class="moh-footer-title">បណ្តាញសង្គម</h3>
          <div class="moh-social-icons">
            <a :href="contact.facebook || 'https://www.facebook.com/profile.php?id=100068634422929'" target="_blank" rel="noopener noreferrer" class="moh-social-btn" title="Facebook">
              <svg viewBox="0 0 24 24" fill="#0a7c5a" width="18" height="18"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
            </a>
            <a :href="contact.telegram || 'https://t.me/kcnprh2022'" target="_blank" rel="noopener noreferrer" class="moh-social-btn" title="Telegram">
              <svg viewBox="0 0 24 24" fill="#0a7c5a" width="18" height="18"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </a>
            <a :href="contact.tiktok || 'https://www.tiktok.com/@kcnprh'" target="_blank" rel="noopener noreferrer" class="moh-social-btn" title="TikTok">
              <svg viewBox="0 0 24 24" fill="#0a7c5a" width="16" height="16"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.298 0 .586.046.86.13V9.4a6.33 6.33 0 0 0-1.07-.09A6.34 6.34 0 0 0 3 15.65a6.34 6.34 0 0 0 10.82 4.47 6.27 6.27 0 0 0 1.96-4.52V8.78a8.18 8.18 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-.96-.21z"/></svg>
            </a>
            <a :href="contact.youtube || 'https://www.youtube.com/@3k3n0r'" target="_blank" rel="noopener noreferrer" class="moh-social-btn" title="YouTube">
              <svg viewBox="0 0 24 24" fill="#0a7c5a" width="18" height="18"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            </a>
          </div>
          <div class="moh-visitor-counter">
            <span>® ចំនួនអ្នកចូលទស្សនា: <strong>{{ visitorCount }}</strong></span>
          </div>
        </div>
      </div>

      <!-- Bottom Sub-footer -->
      <div class="moh-sub-footer">
        <div class="moh-sub-footer-container">
          <p>2026 © រក្សាសិទ្ធិគ្រប់យ៉ាងដោយ {{ site?.khmerName || "មន្ទីរពេទ្យបង្អែកខេត្តកំពង់ឆ្នាំង" }}</p>
          <a href="/admin" class="moh-admin-link">គ្រប់គ្រងប្រព័ន្ធ (Admin)</a>
        </div>
      </div>
    </footer>

    <!-- Back to top floating button -->
    <button
      v-show="showScrollTop"
      class="moh-scroll-to-top"
      type="button"
      aria-label="Scroll to top"
      @click="scrollToTop"
    >
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#0a7c5a" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="18 15 12 9 6 15"></polyline>
      </svg>
    </button>
  </div>
</template>
