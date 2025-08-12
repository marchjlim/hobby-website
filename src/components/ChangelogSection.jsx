
export const ChangelogSection = () => {
  const changelog = [
    // {
    //   version: "v1.2.0",
    //   date: "2025-06-19",
    //   changes: {
    //     Added: [
    //       "Admin dashboard for listing control",
    //       "PayNow QR payment integration (static)",
    //       "Tooltip on Carousell logo"
    //     ],
    //     Fixed: [
    //       "Cancel button in edit listing form now triggers onCancel properly"
    //     ],
    //     Changed: [
    //       "ListingForm tags now scroll horizontally"
    //     ]
    //   }
    // },
    {
      version: "v1.1.0",
      date: "12-08-2025",
      changes: {
        Added: [
            "Telegram link for each listing",
            "Price tag for Telegram vs Carousell",
            "Restocking badge for listings that are restocking",
        ],
      },
    },

    {
      version: "v1.0.0",
      date: "19-06-2025",
      changes: {
        Launch: [
            "Filter function to filter listings using tags",
            "Links to official carousell listings",
            "Light and Dark mode support to enhance browsing experience",
        ],
        Notes: [
            "Account feature currently only supports admin usage.",
        ],
        Upcoming: [
            "PayNow integration to better support shopping experience",
            "Improved filter function to allow users to filter using more than one tag at a time",
        ]
      },
    }
  ];

  return (
    <section id="changelog" className="max-w-4xl mx-auto px-4 py-12 space-y-8">
      <h2 className="text-3xl font-bold text-primary text-center">Changelog</h2>

      {changelog.map((entry, idx) => (
        <div
          key={idx}
          className="border border-border rounded-2xl p-6 bg-muted text-foreground shadow-md space-y-4"
        >
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-semibold">{entry.version}</h3>
            <span className="text-sm text-muted-foreground">{entry.date}</span>
          </div>

          {Object.entries(entry.changes).map(([section, items], i) => (
            <div key={i}>
              <h4 className="text-lg font-semibold text-secondary mb-1">{section}</h4>
              <ul className="list-disc list-inside space-y-1">
                {items.map((item, j) => (
                  <li key={j}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ))}
    </section>
  );
};
