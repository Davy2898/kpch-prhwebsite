<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
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
const site = ref(null);
const postsData = ref({ posts: [], trending: [], categories: [], pagination: {} });
const postDetail = ref(null);
const pageDetail = ref(null);
const selectedService = ref(null);
const loading = ref(true);
const menuOpen = ref(false);
const searchText = ref(route.query.q || "");
const appointmentStatus = ref(null);
const appointmentLoading = ref(false);
const aimNssfOpen = ref(false);
const aimNssfChecklistOpen = ref(false);
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
  if (route.path.startsWith("/search") || activeCategory.value) return pageTitle.value;
  return "Hospital News & Announcements";
});
const featuredPost = computed(() => postsData.value.posts[0] || null);
const updatePosts = computed(() => postsData.value.posts.slice(featuredPost.value ? 1 : 0));
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
const facebookFeedEnabled = false;
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

function csrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "";
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function loadSite() {
  site.value = await fetchJson("/api/site");
}

async function loadPosts() {
  const params = new URLSearchParams();
  params.set("page", route.query.page || "1");
  if (route.query.q) params.set("q", route.query.q);
  if (categoryId.value) params.set("category_id", String(categoryId.value));
  postsData.value = await fetchJson(`/api/posts?${params.toString()}`);
}

async function loadPostDetail() {
  postDetail.value = null;
  if (pathMode.value === "post") {
    const data = await fetchJson(`/api/posts/${route.params.id}`);
    postDetail.value = data;
  }
}

async function loadPageDetail() {
  pageDetail.value = null;
  if (pathMode.value === "page") {
    const data = await fetchJson(`/api/pages/${route.params.slug}`);
    pageDetail.value = data.page;
  }
}

async function loadAll() {
  loading.value = true;
  try {
    await loadSite();
    await loadPosts();
    await Promise.all([loadPostDetail(), loadPageDetail()]);
  } finally {
    loading.value = false;
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

async function submitAppointment() {
  appointmentLoading.value = true;
  appointmentStatus.value = null;
  try {
    const data = await fetchJson("/api/appointments", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
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

onMounted(loadAll);
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
        <RouterLink to="/about">About</RouterLink>
        <RouterLink to="/contact">Contact</RouterLink>
        <a href="/admin">Admin</a>
        <form class="mobile-search" @submit.prevent="goSearch">
          <Search :size="18" />
          <input v-model="searchText" type="search" placeholder="Search news" />
        </form>
      </nav>

      <form class="searchbar" @submit.prevent="goSearch">
        <Search :size="18" />
        <input v-model="searchText" type="search" placeholder="Search news" />
      </form>

      <button class="icon-button menu-button" type="button" aria-label="Menu" @click="menuOpen = !menuOpen">
        <X v-if="menuOpen" :size="22" />
        <Menu v-else :size="22" />
      </button>
    </header>

    <main v-if="!loading">
      <section v-if="isLanding" class="hero">
        <img :src="site?.heroImage" alt="" />
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
            <img :src="service.image" :alt="service.title" />
            <div class="emergency-service-overlay"></div>
            <div class="emergency-service-content">
              <span class="emergency-service-icon">
                <component :is="serviceIcon(service.details.icon)" :size="22" />
              </span>
              <div>
                <strong>{{ service.khmer }}</strong>
                <small>{{ service.title }}</small>
              </div>
              <p>{{ service.details.description }}</p>
              <span class="emergency-service-link">បើកមើលសេវា <ArrowRight :size="15" /></span>
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
              <img :src="service.image" :alt="service.title" />
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

      <section v-if="pathMode === 'home'" :class="['section', 'news-layout', { 'with-facebook': showFacebookFeed }]">
        <div class="content-column">
          <div class="section-heading">
            <p class="eyebrow"><Newspaper :size="18" /> Hospital Updates</p>
            <h2>{{ updatesHeading }}</h2>
            <span class="section-subtitle">Latest hospital announcements, health education, and public service notices.</span>
          </div>
          <div class="updates-overview">
            <div class="updates-notice">
              <ShieldCheck :size="18" />
              <span>Verified updates from Kampong Chhnang Provincial Referral Hospital for patients, families, and visitors.</span>
            </div>
            <div class="updates-mini-stats" aria-label="Hospital update summary">
              <span><strong>{{ postsData.posts.length + 1 }}</strong> Updates</span>
              <span><Clock3 :size="15" /> Latest first</span>
            </div>
          </div>
          <article class="nssf-update-card">
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
          <div v-if="featuredPost" class="featured-grid">
            <RouterLink class="featured-card" :to="featuredPost.url">
              <div class="featured-media">
                <img v-if="featuredPost.image" :src="featuredPost.image" :alt="featuredPost.title" />
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
            <RouterLink v-for="post in updatePosts" :key="post.id" class="post-card" :to="post.url">
              <div class="post-card-media">
                <img v-if="post.image" :src="post.image" :alt="post.title" />
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
          <div v-if="postsData.pagination.pages > 1" class="pager">
            <button :disabled="!postsData.pagination.hasPrev" @click="setPage(postsData.pagination.page - 1)">
              <ArrowLeft :size="18" /> Prev
            </button>
            <span>{{ postsData.pagination.page }} / {{ postsData.pagination.pages }}</span>
            <button :disabled="!postsData.pagination.hasNext" @click="setPage(postsData.pagination.page + 1)">
              Next <ArrowRight :size="18" />
            </button>
          </div>
        </div>

        <aside v-if="showFacebookFeed" class="facebook-feed-panel" aria-labelledby="facebook-feed-title">
          <div class="facebook-feed-header">
            <div>
              <p class="eyebrow"><Facebook :size="18" /> Facebook</p>
              <h3 id="facebook-feed-title">Real-Time Facebook Updates</h3>
            </div>
            <a :href="contact.facebook" target="_blank" rel="noopener">
              View Page <ArrowRight :size="15" />
            </a>
          </div>
          <div class="facebook-frame-wrap">
          <iframe
            title="Latest Facebook posts"
            :src="facebookFeedUrl"
            width="500"
            height="900"
            style="border: none; overflow: hidden"
            scrolling="no"
            frameborder="0"
            allowfullscreen="true"
            allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
          ></iframe>
          </div>
        </aside>

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
            <img :src="activeService.image" :alt="activeService.title" />
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
            <img :src="director.image" :alt="director.name" />
            <strong>{{ director.khmer }}</strong>
            <span>{{ director.name }}</span>
            <small>{{ director.role }}</small>
          </article>
        </div>
        <div class="leaders-grid">
          <article v-for="leader in viceLeaders" :key="leader.name" class="leader-card">
            <img :src="leader.image" :alt="leader.name" />
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
            <img :src="site?.heroImage" alt="" />
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
        <RouterLink class="back-link" to="/"><ArrowLeft :size="18" /> Back to news</RouterLink>
        <img v-if="postDetail.post.image" :src="postDetail.post.image" :alt="postDetail.post.title" />
        <p class="eyebrow"><Newspaper :size="18" /> {{ postDetail.post.category?.name || "News" }}</p>
        <h1>{{ postDetail.post.title }}</h1>
        <div class="post-meta">{{ postDetail.post.date }} · {{ postDetail.post.views }} views</div>
        <div v-if="isAimNssfPost" class="aim-post-action-panel">
          <div>
            <strong>{{ aimNssfUpdate.stepsTitle }}</strong>
            <span>{{ aimNssfUpdate.status }} · {{ aimNssfUpdate.location }}</span>
          </div>
          <button class="aim-checklist-button" type="button" @click="aimNssfChecklistOpen = true">
            <CheckCircle2 :size="18" /> បើកបញ្ជីឯកសារត្រូវត្រៀម
          </button>
        </div>
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
        <article class="post-body" v-html="postDetail.post.body"></article>
      </section>

      <section v-if="pathMode === 'page'" class="section static-page">
        <h1>{{ pageDetail?.title || "Page not found" }}</h1>
        <article v-if="pageDetail" v-html="pageDetail.body"></article>
      </section>
    </main>

    <main v-else class="loading-view">
      <div></div>
      <span>Loading</span>
    </main>

    <footer class="footer">
      <div>
        <strong>{{ site?.khmerName || "មន្ទីរពេទ្យខេត្តកំពង់ឆ្នាំង" }}</strong>
        <span>{{ contact.address }}</span>
      </div>
      <div>
        <RouterLink to="/about">About</RouterLink>
        <RouterLink to="/contact">Contact</RouterLink>
        <a href="/admin">Admin</a>
      </div>
    </footer>
  </div>
</template>
